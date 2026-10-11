from io import BytesIO
import zipfile


def archive(entries):
    output = BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as package:
        for name, content in entries.items():
            package.writestr(name, content)
    return output.getvalue()


def office_files():
    return {
        'report.docx': archive({'word/document.xml': '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>会议结论：下周上线。</w:t></w:r></w:p></w:body></w:document>'}),
        'sales.xlsx': archive({
            'xl/workbook.xml': '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="销售" sheetId="1" r:id="rId1"/></sheets></workbook>',
            'xl/_rels/workbook.xml.rels': '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>',
            'xl/sharedStrings.xml': '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>茶</t></si></sst>',
            'xl/worksheets/sheet1.xml': '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>咖啡</t></is></c><c r="B1"><v>17</v></c></row><row r="2"><c r="A2" t="s"><v>0</v></c><c r="B2"><v>23</v></c></row><row r="3"><c r="B3"><f>SUM(B1:B2)</f><v>40</v></c></row></sheetData></worksheet>',
        }),
        'slides.pptx': archive({'ppt/slides/slide1.xml': '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:t>项目进展：验证通过。</a:t></p:sld>'}),
    }


def pdf_file(text='Invoice total: 84731', scanned=False):
    import pymupdf
    with pymupdf.open() as pdf:
        page = pdf.new_page(width=600, height=400)
        if scanned:
            from PIL import Image, ImageDraw, ImageFont
            image = Image.new('RGB', (1200, 800), 'white')
            font = ImageFont.truetype('/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf', 72)
            ImageDraw.Draw(image).text((80, 160), text, fill='black', font=font)
            output = BytesIO()
            image.save(output, format='PNG')
            page.insert_image(page.rect, stream=output.getvalue())
        else:
            page.insert_text((40, 120), text, fontsize=24)
        return pdf.tobytes()
