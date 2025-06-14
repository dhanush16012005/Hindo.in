from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define the database URI
DATABASE_URI = 'sqlite:///instance/hindo.db'

# Create an engine
engine = create_engine(DATABASE_URI, echo=True)

# Define a base class for declarative class definitions
Base = declarative_base()

# Define the Course class
class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    published = Column(Boolean, nullable=False, default=False)

# Create the courses table
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Example to add a new course
new_course = Course(name="Example Course")
session.add(new_course)
session.commit()

# Close the session
session.close()

print("Courses table created successfully with initial data.")
