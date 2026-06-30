# DOCX creation, editing, and analysis — 详细参考

本文件是 `docx-cn` Skill 的详细用法参考。如果你只想知道触发条件和快速入口，请阅读 [`SKILL.md`](./SKILL.md)。

---

## 概述

`.docx` 文件本质上是一个 ZIP 压缩包，内部包含 XML 文件。处理方式分三类：
- **读取/分析**：`pandoc` 或解压看 XML
- **新建文档**：使用 `docx-js`（npm `docx` 包）
- **编辑已有文档**：解压 → 编辑 XML → 重新打包

---

## 读取内容

### 提取文本（保留修订）

```bash
pandoc --track-changes=all document.docx -o output.md
```

### 解压查看原始 XML

```bash
python scripts/office/unpack.py document.docx unpacked/
```

### 接受所有修订

```bash
python scripts/accept_changes.py input.docx output.docx
```

### `.doc` 转 `.docx`

```bash
python scripts/office/soffice.py --headless --convert-to docx document.doc
```

### 转为图片

```bash
python scripts/office/soffice.py --headless --convert-to pdf document.docx
pdftoppm -jpeg -r 150 document.pdf page
```

---

## 创建新文档（docx-js）

安装：`npm install -g docx`

### 基础结构

```javascript
const { Document, Packer, Paragraph, TextRun } = require('docx');

const doc = new Document({
  sections: [{
    children: [new Paragraph({ children: [new TextRun("Hello")] })]
  }]
});

Packer.toBuffer(doc).then(buffer => fs.writeFileSync("doc.docx", buffer));
```

### 验证生成文件

```bash
python scripts/office/validate.py doc.docx
```

### 页面尺寸

```javascript
sections: [{
  properties: {
    page: {
      size: {
        width: 12240,   // 8.5 英寸 DXA
        height: 15840   // 11 英寸 DXA
      },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
    }
  },
  children: [/* content */]
}]
```

常见尺寸：

| 纸张 | 宽 | 高 | 内容宽（1 英寸边距） |
|------|----|----|---------------------|
| US Letter | 12,240 | 15,840 | 9,360 |
| A4（默认） | 11,906 | 16,838 | 9,026 |

横向页面：

```javascript
size: {
  width: 12240,
  height: 15840,
  orientation: PageOrientation.LANDSCAPE  // docx-js 内部会交换宽高
}
```

### 样式与标题

```javascript
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 } },
    ]
  }
});
```

### 列表

```javascript
const doc = new Document({
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  sections: [{
    children: [
      new Paragraph({ numbering: { reference: "bullets", level: 0 },
        children: [new TextRun("Bullet item")] }),
    ]
  }]
});
```

### 表格

```javascript
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [4680, 4680],
  rows: [
    new TableRow({
      children: [
        new TableCell({
          borders,
          width: { size: 4680, type: WidthType.DXA },
          shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun("Cell")] })]
        })
      ]
    })
  ]
})
```

### 图片

```javascript
new Paragraph({
  children: [new ImageRun({
    type: "png",
    data: fs.readFileSync("image.png"),
    transformation: { width: 200, height: 150 },
    altText: { title: "Title", description: "Desc", name: "Name" }
  })]
})
```

### 分页、目录、页眉页脚

```javascript
// 分页
new Paragraph({ children: [new PageBreak()] })

// 目录
new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" })

// 页眉页脚
sections: [{
  headers: { default: new Header({ children: [new Paragraph({ children: [new TextRun("Header")] })] }) },
  footers: { default: new Footer({ children: [new Paragraph({
    children: [new TextRun("Page "), new TextRun({ children: [PageNumber.CURRENT] })]
  })] }) },
  children: [/* content */]
}]
```

---

## 编辑已有文档

### 三步流程

1. **解压**
   ```bash
   python scripts/office/unpack.py document.docx unpacked/
   ```

2. **编辑 XML**
   - 直接编辑 `unpacked/word/` 下的 XML
   - 修订作者默认使用 "Claude"
   - 新增内容使用智能引号 XML 实体：
     - `&#x2018;` ‘
     - `&#x2019;` ’
     - `&#x201C;` “
     - `&#x201D;` ”

3. **打包**
   ```bash
   python scripts/office/pack.py unpacked/ output.docx --original document.docx
   ```

### 添加批注

```bash
python scripts/comment.py unpacked/ 0 "Comment text"
python scripts/comment.py unpacked/ 1 "Reply" --parent 0
```

---

## XML 参考

### 修订标记

```xml
<!-- 插入 -->
<w:ins w:id="1" w:author="Claude" w:date="2025-01-01T00:00:00Z">
  <w:r><w:t>inserted text</w:t></w:r>
</w:ins>

<!-- 删除 -->
<w:del w:id="2" w:author="Claude" w:date="2025-01-01T00:00:00Z">
  <w:r><w:delText>deleted text</w:delText></w:r>
</w:del>
```

### 批注标记

```xml
<w:commentRangeStart w:id="0"/>
<w:r><w:t>text</w:t></w:r>
<w:commentRangeEnd w:id="0"/>
<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="0"/></w:r>
```

### 图片引用

```xml
<w:drawing>
  <wp:inline>
    <wp:extent cx="914400" cy="914400"/>
    <a:graphic>
      <a:graphicData uri=".../picture">
        <pic:pic>
          <pic:blipFill><a:blip r:embed="rId5"/></pic:blipFill>
        </pic:pic>
      </a:graphicData>
    </a:graphic>
  </wp:inline>
</w:drawing>
```

---

## 依赖

- **pandoc**：文本提取
- **docx**：`npm install -g docx`（新建文档）
- **LibreOffice**：PDF 转换（通过 `scripts/office/soffice.py`）
- **Poppler**：`pdftoppm` 转图片
