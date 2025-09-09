import pdfplumber
from docx import Document

from pdf2docx import Converter
import win32com.client

if __name__ == '__main__':

    pdf = pdfplumber.open(r'D:\rj\xwechat_files\wxid_cuf9ncpdrhbc22_a926\msg\file\2025-08\张文栋-java研发工程师 .pdf')
    # doc = Document()
    #
    # for page in pdf.pages:
    #     text = page.extract_text()
    #     if text:
    #         doc.add_paragraph(text)
    #
    # pdf.close()
    # doc.save('output.docx')

    # pdf_file = r'D:\rj\weixin\WeChat Files\wxid_cuf9ncpdrhbc22\FileStorage\File\2025-07\李兰简历 (1).pdf'
    # docx_file = 'output.docx'
    #
    # cv = Converter(pdf_file)
    # cv.convert(docx_file, start=0, end=None)  # 转全部页
    # cv.close()

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False

    pdf_path = r'D:\rj\xwechat_files\wxid_cuf9ncpdrhbc22_a926\msg\file\2025-08\张文栋-java研发工程师 .pdf'
    docx_path = r'D:\rj\py\PycharmProjects\PythonProject\dist\file1.docx'

    doc = word.Documents.Open(pdf_path)
    doc.SaveAs(docx_path, FileFormat=16)  # 16=wdFormatDocumentDefault
    doc.Close()

    word.Quit()