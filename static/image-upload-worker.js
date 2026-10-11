'use strict';
// Keep decoding/encoding away from the conversation UI. Never resize pixels.
self.onmessage = async ({data: file}) => {
  let bitmap;
  try {
    const header = new Uint8Array(await file.arrayBuffer());
    const jpeg = header[0] === 255 && header[1] === 216;
    const png = header[0] === 137 && header[1] === 80 && header[2] === 78 && header[3] === 71;
    if (!jpeg && !png) { self.postMessage(file); return; }
    if (png) {
      const view = new DataView(header.buffer);
      // Preserve animated PNGs instead of silently keeping just one frame.
      for (let offset = 8; offset + 12 <= header.length;) {
        if (view.getUint32(offset + 4) === 0x6163544c) { self.postMessage(file); return; }
        const length = view.getUint32(offset); offset += length + 12;
      }
    }
    bitmap = await createImageBitmap(file);
    if (bitmap.width * bitmap.height > 40000000) { self.postMessage(file); return; }
    const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
    canvas.getContext('2d').drawImage(bitmap, 0, 0);
    const blob = await canvas.convertToBlob({type: jpeg ? 'image/jpeg' : 'image/webp', quality: jpeg ? 0.92 : 0.96});
    // Only pay the quality tradeoff if the transfer shrinks substantially.
    self.postMessage(blob.size < file.size * 0.85 ? blob : file);
  } catch { self.postMessage(file); }
  finally { bitmap?.close(); }
};
