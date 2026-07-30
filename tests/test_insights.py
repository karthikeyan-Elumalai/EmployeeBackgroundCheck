import unittest

from src.insights import build_resume_insights


class InsightsParsingTests(unittest.TestCase):
    def test_core_skills_markdown_section_is_extracted(self):
        resume_text = """
# John Anderson

# Core Skills
* Java, Python, JavaScript, TypeScript
* Spring Boot, Hibernate
* React.js, Angular
* REST APIs, Microservices
* SQL, PostgreSQL, MySQL
* Docker, Kubernetes

# Professional Experience
Senior Software Engineer with 10 years of experience.

# Education
Master of Science in Computer Science
"""
        insights = build_resume_insights(resume_text)
        top_skills = [item["skill"] for item in insights["top_skills"]]

        self.assertIn("python", top_skills)
        self.assertIn("java", top_skills)
        self.assertIn("docker", top_skills)
        self.assertIn("kubernetes", top_skills)
        self.assertEqual(insights["experience_levels"]["senior"], 1)
        self.assertEqual(insights["education_levels"]["masters"], 1)


if __name__ == "__main__":
    unittest.main()
