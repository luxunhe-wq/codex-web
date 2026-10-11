"""Bounded document extraction in a separate process; never execute uploaded files."""
from io import BytesIO
import json
import os
from pathlib import Path
import re
import resource
import sys
from xml.etree import ElementTree as ET
import zipfile

MAX_TEXT = 120_000
MAX_EXPANDED = 50 * 1024 * 1024
MAX_MEMBER = 8 * 1024 * 1024


def decode_text(data):
    encodings = ('utf-16',) if data.startswith((b'\xff\xfe', b'\xfe\xff')) else ('utf-8-sig', 'gb18030')
    for encoding in encodings:
        try:
            text = data.decode(encoding)
            if sum(ord(char) < 32 and char not in '\n\r\t' for char in text[:4096]) > 8:
                return None
            return text
        except UnicodeError:
            continue
    return None


def extract_document(data, name, output):
    extension = Path(name).suffix.lower()
    result = {'text': '', 'truncated': False, 'pages': 0, 'scanPages': [], 'note': '', 'format': extension.lstrip('.') or 'file'}
    chunks = []
    length = 0

    def add(text):
        nonlocal length
        if not text:
            return
        available = MAX_TEXT - length
        if len(text) > available:
            result['truncated'] = True
        if available > 0:
            chunks.append(text[:available])
            length += len(chunks[-1])

    if data.startswith(b'%PDF-') or extension == '.pdf':
        import pymupdf
        try:
            with pymupdf.open(stream=data, filetype='pdf') as document:
                if document.needs_pass:
                    raise ValueError('PDF 已加密，请先解密后上传')
                result['format'] = 'pdf'
                result['pages'] = len(document)
                result['truncated'] = len(document) > 50
                for index in range(min(50, len(document))):
                    if length >= MAX_TEXT:
                        result['truncated'] = True
                        break
                    page = document[index]
                    text = page.get_text(sort=True)
                    add('\n[第 %d 页]\n%s' % (index + 1, text))
                    if len(text.strip()) < 50:
                        if len(result['scanPages']) >= 4:
                            result['truncated'] = True
                            continue
                        scale = min(2, 1600 / max(page.rect.width, page.rect.height, 1))
                        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
                        path = output / ('page-%d.png' % (index + 1))
                        pixmap.save(path)
                        os.chmod(path, 0o600)
                        result['scanPages'].append(index + 1)
        except ValueError:
            raise
        except Exception:
            raise ValueError('PDF 无法读取，请检查文件是否损坏')
    elif extension in ('.docx', '.xlsx', '.pptx', '.zip'):
        try:
            with zipfile.ZipFile(BytesIO(data)) as archive:
                members = archive.infolist()
                if len(members) > 1024 or sum(member.file_size for member in members) > MAX_EXPANDED:
                    raise ValueError('文件解压后的内容过大，请拆分后上传')

                def read(member):
                    with archive.open(member) as file:
                        body = file.read(MAX_MEMBER + 1)
                    if len(body) > MAX_MEMBER:
                        raise ValueError('文件内部内容过大，请拆分后上传')
                    return body

                def xml(member):
                    body = read(member)
                    if b'<!DOCTYPE' in body.upper() or b'<!ENTITY' in body.upper():
                        raise ValueError('文档 XML 格式不受支持')
                    return ET.fromstring(body)

                if extension == '.docx':
                    tree = xml('word/document.xml')
                    for paragraph in tree.iter():
                        if paragraph.tag.endswith('}p'):
                            add(''.join(node.text or '' for node in paragraph.iter() if node.tag.endswith('}t')) + '\n')
                elif extension == '.pptx':
                    slides = sorted((member.filename for member in members if re.fullmatch(r'ppt/slides/slide\d+\.xml', member.filename)),
                                    key=lambda value: int(re.search(r'slide(\d+)\.xml', value).group(1)))
                    if not slides:
                        raise ValueError('PowerPoint 文档没有可读取的幻灯片')
                    result['pages'] = len(slides)
                    for index, slide in enumerate(slides):
                        add('\n[幻灯片 %d]\n' % (index + 1))
                        for node in xml(slide).iter():
                            if node.tag.endswith('}t'):
                                add((node.text or '') + '\n')
                elif extension == '.xlsx':
                    names = archive.namelist()
                    workbook = xml('xl/workbook.xml')
                    relationships = {node.get('Id'): node.get('Target', '') for node in xml('xl/_rels/workbook.xml.rels')
                                     if node.get('TargetMode') != 'External'}
                    strings = [''.join(node.text or '' for node in item.iter() if node.tag.endswith('}t'))
                               for item in xml('xl/sharedStrings.xml')] if 'xl/sharedStrings.xml' in names else []
                    for sheet in workbook.iter():
                        if not sheet.tag.endswith('}sheet'):
                            continue
                        relation = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                        target = relationships.get(relation, '')
                        member = target.lstrip('/') if target.startswith('/') else 'xl/' + target.removeprefix('./')
                        if member not in names:
                            raise ValueError('Excel 工作表无法读取')
                        add('\n[工作表 %s]\n' % sheet.get('name', 'Sheet'))
                        for row in xml(member).iter():
                            if not row.tag.endswith('}row'):
                                continue
                            cells = []
                            for cell in row:
                                value = next((node.text or '' for node in cell if node.tag.endswith('}v')), '')
                                formula = next((node.text or '' for node in cell if node.tag.endswith('}f')), '')
                                if cell.get('t') == 's':
                                    value = strings[int(value)]
                                elif cell.get('t') == 'inlineStr':
                                    value = ''.join(node.text or '' for node in cell.iter() if node.tag.endswith('}t'))
                                if formula:
                                    value += ' [公式: ' + formula + ']'
                                cells.append('%s=%s' % (cell.get('r', ''), value))
                            add('\t'.join(cells) + '\n')
                else:
                    add('[ZIP 文件目录]\n' + '\n'.join(member.filename for member in members) + '\n')
                    for member in members:
                        if member.is_dir() or member.file_size > MAX_MEMBER or length >= MAX_TEXT:
                            continue
                        text = decode_text(read(member))
                        if text is not None:
                            add('\n[文件 %s]\n%s\n' % (member.filename, text))
        except ValueError:
            raise
        except Exception:
            raise ValueError('文档无法读取，请检查格式或文件是否损坏')
    else:
        text = decode_text(data)
        if text is None or data.startswith((b'MZ', b'\x7fELF', b'\xd0\xcf\x11\xe0')):
            result['note'] = '此格式未自动提取文本，Codex 可以按需读取原文件。'
        else:
            add(text)
    result['text'] = ''.join(chunks)
    if result['truncated']:
        result['note'] = '文件较长，当前展示部分内容，原文件已保留供继续读取。'
    return result


if __name__ == '__main__':
    resource.setrlimit(resource.RLIMIT_AS, (768 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    resource.setrlimit(resource.RLIMIT_FSIZE, (20 * 1024 * 1024,) * 2)
    request = json.loads(sys.stdin.read())
    try:
        result = extract_document(Path(request['path']).read_bytes(), request['name'], Path(request['output']))
        print(json.dumps({'analysis': result}, ensure_ascii=False))
    except Exception as error:
        print(json.dumps({'error': str(error) if isinstance(error, ValueError) else '文件内容无法读取'}, ensure_ascii=False))
