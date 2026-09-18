import asyncio
from app.db.session import AsyncSessionLocal, engine
from app.models.domain import Base, Student, Exam, Question, ReferenceAnswer

async def seed():
    async with AsyncSessionLocal() as session:
        # Create some students
        students = [
            Student(name="Aarav Sharma", roll_no="101"),
            Student(name="Vivaan Gupta", roll_no="102"),
            Student(name="Diya Patel", roll_no="103"),
            Student(name="Ananya Singh", roll_no="104"),
            Student(name="Arjun Reddy", roll_no="105"),
        ]
        session.add_all(students)
        await session.commit()
        
        # Create an exam
        exam = Exam(name="Midterm Biology - Class 10")
        session.add(exam)
        await session.commit()
        await session.refresh(exam)
        
        # Create a question
        question = Question(exam_id=exam.id, text="प्रकाश संश्लेषण क्या है?", max_marks=10.0)
        session.add(question)
        await session.commit()
        await session.refresh(question)
        
        # Create a reference answer
        ref_answer = ReferenceAnswer(
            question_id=question.id,
            text="प्रकाश संश्लेषण वह प्रक्रिया है जिसके द्वारा हरे पौधे सूर्य के प्रकाश की उपस्थिति में जल एवं कार्बन डाइआक्साइड के संयोग से कार्बोहाइड्रेट का निर्माण करते हैं तथा इस प्रक्रिया में आक्सीजन गैस बाहर निकलती है।",
            rubric_keywords=["photosynthesis", "sunlight", "carbon dioxide", "oxygen", "water", "carbohydrates"]
        )
        session.add(ref_answer)
        await session.commit()
        
        print("Database successfully seeded!")
        print(f"Exam ID: {exam.id}")
        print(f"Question ID: {question.id}")
        print("Student Roll Nos:", [s.roll_no for s in students])

if __name__ == "__main__":
    asyncio.run(seed())
