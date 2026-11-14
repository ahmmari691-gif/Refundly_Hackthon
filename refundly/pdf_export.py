"""Generate transient PDF documents in memory; nothing is saved by the API."""
from io import BytesIO
from xml.sax.saxutils import escape

def document_pdf(text, title='Security deposit correspondence'):
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    output=BytesIO()
    doc=SimpleDocTemplate(output,pagesize=(612,792),rightMargin=54,leftMargin=54,topMargin=83,bottomMargin=55,title='Refundly - '+title,author='Refundly')
    styles=getSampleStyleSheet()
    style=ParagraphStyle('Letter',parent=styles['Normal'],fontName='Helvetica',fontSize=10.5,leading=16,textColor=colors.HexColor('#303951'),spaceAfter=7,splitLongWords=True)
    story=[]
    for line in text.replace('\r','').split('\n'):
        if line.strip():story.append(Paragraph(escape(line),style))
        else:story.append(Spacer(1,7))
    def decorate(canvas,doc):
        canvas.saveState();canvas.setFillColor(colors.HexColor('#2d3558'));canvas.setFont('Helvetica-Bold',18);canvas.drawString(54,750,'Refundly');canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#8991a5'));canvas.drawRightString(558,752,title[:70]);canvas.setStrokeColor(colors.HexColor('#dfdce4'));canvas.line(54,731,558,731);canvas.setFont('Helvetica',8);canvas.drawString(54,30,'Prepared by the sender using Refundly document tools.');canvas.drawRightString(558,30,str(doc.page));canvas.restoreState()
    doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
    return output.getvalue()
