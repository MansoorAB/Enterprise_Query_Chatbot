from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
import argparse


class PolicyGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.styles = self._get_sample_styles()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)


    def _get_sample_styles(self):
        """Initialize document styles"""
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='CustomTitle',
            fontSize=24,
            spaceAfter=30,
            alignment=1
        ))
        return styles


    def generate_hr_policy(self):
        """Generate HR policy document"""
        doc = SimpleDocTemplate(os.path.join(self.output_dir, "hr_policy.pdf"), pagesize=letter)
        story = []

        # Title
        story.append(Paragraph("Human Resources Policy", self.styles['Title']))
        story.append(Spacer(1, 12))
        
        # Add content sections
        sections = [
            ("1. Code of Conduct", """
            All employees must maintain professional behavior and respect workplace ethics. 
            This includes maintaining confidentiality, avoiding conflicts of interest, 
            and promoting a harassment-free environment.
            """),
            ("2. Leave Policy", """
            Employees are entitled to the following leave benefits:
            • 20 days of annual leave
            • 10 days of sick leave
            • 10 days of personal leave
            """),
        ]
        
        for title, content in sections:
            story.append(Paragraph(title, self.styles['Heading1']))
            story.append(Paragraph(content, self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Add a sample table
        data = [
            ['Leave Type', 'Days per Year', 'Carry Forward'],
            ['Annual', '20', 'Up to 5 days'],
            ['Sick', '10', 'None'],
            ['Personal', '10', 'Up to 5 days'],
        ]
        table = Table(data)
        table.setStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ])
        story.append(table)
        
        doc.build(story)
        print(f"Generated HR policy at: {doc.filename}")


    def generate_travel_policy(self):
        """Generate travel policy document"""
        doc = SimpleDocTemplate(os.path.join(self.output_dir, "travel_policy.pdf"), pagesize=letter)
        story = []
        
        story.append(Paragraph("Travel Policy", self.styles['Title']))
        story.append(Spacer(1, 12))
        
        content = """
        1. Travel Booking
        All business travel must be booked through the company's approved travel portal.
        
        2. Expense Limits
        • Hotel: Up to $300 per night
        • Meals: Up to $75 per day
        • Transportation: Economy class for flights under 6 hours
        """
        
        story.append(Paragraph(content, self.styles['Normal']))
        doc.build(story)
        print(f"Generated travel policy at: {doc.filename}")


    def generate_compensation_policy(self):
        """Generate compensation policy document"""
        doc = SimpleDocTemplate(os.path.join(self.output_dir, "compensation_policy.pdf"), pagesize=letter)
        story = []
        
        story.append(Paragraph("Compensation Policy", self.styles['Title']))
        story.append(Spacer(1, 12))
        
        # Add salary structure table
        data = [
            ['Level', 'Base Salary Range', 'Bonus Range'],
            ['Entry', '$40,000 - $60,000', '5-10%'],
            ['Mid', '$60,000 - $90,000', '10-15%'],
            ['Senior', '$90,000 - $130,000', '15-20%'],
        ]
        table = Table(data)
        table.setStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ])
        story.append(table)
        
        doc.build(story)
        print(f"Generated compensation policy at: {doc.filename}")


    def generate_email_policy(self):
        """Generate email policy document"""
        doc = SimpleDocTemplate(os.path.join(self.output_dir, "email_policy.pdf"), pagesize=letter)
        story = []
        
        story.append(Paragraph("Email Communication Policy", self.styles['Title']))
        story.append(Spacer(1, 12))
        
        content = """
        1. Email Usage
        • Use professional language in all communications
        • Include clear subject lines
        • Respond to emails within 24 business hours
        
        2. Security
        • Never share passwords
        • Be cautious with attachments
        • Report suspicious emails to IT
        """
        
        story.append(Paragraph(content, self.styles['Normal']))
        doc.build(story)
        print(f"Generated email policy at: {doc.filename}")


    def generate_all(self):
        """Generate all policy documents"""
        print(f"\nGenerating policy documents in: {self.output_dir}")
        self.generate_hr_policy()
        # self.generate_travel_policy()
        # self.generate_compensation_policy()
        # self.generate_email_policy()
        print("\nAll policy documents have been generated successfully!")


def main():
    parser = argparse.ArgumentParser(
        description="Generate sample policy documents in PDF format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--output-dir",
        default="./data/sample_policies",
        help="Directory where policy documents will be generated"
    )
    
    args = parser.parse_args()
    
    generator = PolicyGenerator(output_dir=args.output_dir)
    generator.generate_all()


if __name__ == "__main__":
    main() 