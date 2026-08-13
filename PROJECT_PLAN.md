# AI-Fitness Project Plan

## Version

**Project Plan Version:** 1.0

This document defines the long-term vision, architecture, features, development roadmap, and learning goals for the AI-Fitness project.

The project will be developed progressively. Features listed here represent the long-term vision and do not need to be implemented at the same time.

---

# 1. Project Goal

Build an evidence-based fitness, nutrition, activity, and progress-tracking platform that combines:

* Scientific research
* User data
* Biometrics
* Exercise data
* Nutrition data
* Activity data
* Recommendation systems
* Data science
* Artificial intelligence
* Computer vision
* Mobile applications
* Wearable devices

The platform should provide personalized fitness and nutrition guidance based on the user's:

* Goals
* Fitness level
* Training experience
* Lifestyle
* Environment
* Schedule
* Exercise preferences
* Nutrition preferences
* Physical limitations
* Previous training
* Previous nutrition data
* Daily activity
* Recovery
* Progress over time

The long-term goal is to create an adaptive fitness platform that improves its recommendations as more information becomes available about the user.

---

# 2. Skills the Project Should Develop

The project should be used as a practical learning environment for:

* Python
* Pandas
* NumPy
* Data cleaning
* Data analysis
* Data visualization
* Statistics
* SQL
* Database design
* Data engineering
* APIs
* Backend development
* Object-oriented programming
* Testing
* Recommendation systems
* Machine learning
* Natural Language Processing
* Embeddings
* Vector databases
* Retrieval-Augmented Generation
* Large Language Models
* Computer vision
* Image processing
* Time-series analysis
* Geospatial/GPS data
* Mobile development
* Wearable integrations
* Privacy and security
* Git
* GitHub
* Software architecture
* Deployment

The goal is not simply to create an application.

The project should demonstrate that the underlying systems are understood.

---

# 3. Core Development Principles

The project should prioritize:

1. Evidence
2. Data quality
3. Personalization
4. Safety
5. Transparency
6. User privacy
7. Explainability
8. Reliable calculations
9. User control
10. Progressive development

Artificial intelligence should be one component of the platform rather than the entire platform.

Important calculations and safety constraints should be handled by structured software logic wherever possible.

---

# 4. User Assessment & Profile

The platform should build a structured profile for every user.

## Personal Information

Potential information includes:

* Age
* Height
* Weight
* Activity level
* Optional body measurements

Users should not be required to provide information that is unnecessary for the features they use.

---

## Fitness Information

Potential information includes:

* Fitness level
* Training experience
* Training frequency
* Current workout routine
* Fitness goals
* Preferred training style
* Available equipment
* Gym access
* Home equipment
* Current strength/performance
* Exercises the user enjoys
* Exercises the user dislikes
* Exercises the user cannot perform
* Preferred activities
* Pain or physical limitations
* Recovery information
* Sleep information

---

## Lifestyle Information

The platform may eventually consider:

* Work schedule
* School schedule
* Commute
* Available workout time
* Typical waking time
* Typical sleeping time
* Daily activity
* Occupation activity level
* Days available for training
* Preferred training times
* Environment
* Access to indoor/outdoor activities

This information will allow recommendations to fit the user's actual lifestyle.

---

## Nutrition Information

Potential information includes:

* Nutrition goals
* Dietary preferences
* Dietary restrictions
* Food allergies
* Foods the user avoids
* Foods the user dislikes
* Foods the user enjoys
* Preferred meals
* Cooking ability
* Cooking time
* Budget
* Available ingredients
* Number of meals preferred
* Daily calorie target
* Macro targets

Food allergies should be treated as hard safety constraints rather than simple preferences.

---

## Safety Information

Pain and physical limitations should influence exercise recommendations.

The application should not diagnose:

* Injuries
* Diseases
* Medical conditions
* Nutrient deficiencies
* Eating disorders

When a user's situation requires medical or clinical assessment, the application should recommend seeking an appropriately qualified professional.

---

# 5. Research & Evidence Database

The research system will form one of the main foundations of AI-Fitness.

The platform should contain a curated database of high-quality research covering fitness, nutrition, recovery, activity, and related topics.

---

## Resistance Training Research

Topics may include:

* Hypertrophy
* Strength
* Training volume
* Training frequency
* Training intensity
* Repetitions
* Sets
* Rest periods
* Progressive overload
* Exercise selection
* Range of motion
* Training to failure
* Exercise order
* Training experience
* Workout splits
* Push / Pull / Legs
* Upper / Lower
* Full-body training

---

## Exercise Physiology

Topics may include:

* Skeletal muscle
* Muscle growth
* Muscle fiber types
* Fatigue
* Energy systems
* Adaptation
* Strength development
* Cardiovascular adaptation
* Movement
* Exercise performance

---

## Nutrition Research

Topics may include:

* Protein
* Carbohydrates
* Dietary fats
* Fiber
* Calories
* Energy balance
* Energy expenditure
* Weight management
* Body recomposition
* Meal timing
* Hydration
* Sports nutrition
* Supplements
* Creatine
* Caffeine

---

## Recovery & Lifestyle Research

Topics may include:

* Sleep
* Recovery
* Training fatigue
* Rest days
* Stress
* Daily activity
* Sedentary behavior
* Healthy lifestyle habits

---

## Research Quality

The database should distinguish between different types of evidence.

Potential study types include:

* Systematic reviews
* Meta-analyses
* Randomized controlled trials
* Controlled trials
* Cohort studies
* Observational studies
* Cross-sectional studies
* Case studies
* Expert consensus
* Professional guidelines

The system should not automatically treat every study as equally strong evidence.

Research recommendations should consider:

* Study design
* Sample size
* Population
* Duration
* Methods
* Limitations
* Consistency with other research
* Applicability to the user

---

## Research Licensing & Attribution

The project should prioritize research that is legally accessible and whose reuse conditions are understood.

For every research source, store information such as:

* Title
* Authors
* Publication year
* Journal
* DOI
* Source URL
* License
* License URL
* Open-access status

AI-Fitness should preferably store structured information and original summaries written in the developer's own words.

Full research PDFs should not be redistributed publicly unless their license explicitly allows redistribution.

Research sources should always be attributed.

---

## Research-to-Recommendation Pipeline

The long-term process should follow:

Research Paper

↓

Research Topic

↓

Research Question

↓

Study Population

↓

Methods

↓

Results

↓

Study Limitations

↓

Evidence Assessment

↓

Practical Interpretation

↓

User Applicability

↓

Recommendation System

Recommendations should preferably use multiple relevant sources rather than relying on one isolated study.

---

# 6. Exercise Database

Create a structured database of exercises.

Potential fields include:

* Exercise ID
* Exercise name
* Primary muscles
* Secondary muscles
* Movement pattern
* Equipment
* Difficulty
* Exercise type
* Compound / isolation
* Free weight / machine / bodyweight
* Unilateral / bilateral
* Exercise alternatives
* Exercise instructions
* Setup instructions
* Common mistakes
* Safety considerations
* Suitable experience level

---

## Exercise Preferences

The system should allow users to specify:

* Exercises they enjoy
* Exercises they dislike
* Exercises they cannot perform
* Equipment they prefer
* Equipment they cannot access

The recommendation system should attempt to provide reasonable alternatives rather than forcing one particular exercise.

---

# 7. Workout System

The workout system should eventually support:

* Personalized workout generation
* Workout templates
* Workout routines
* Exercise selection
* Exercise substitution
* Sets
* Repetitions
* Weight/load
* Rest periods
* Training frequency
* Training volume
* Exercise order
* Progressive overload
* Strength tracking
* Workout logging
* Workout history
* Personal records
* Notes

Users should be able to modify generated workouts.

---

## Workout Timer & Stopwatch

The workout system should include timing utilities.

Potential features include:

* Stopwatch
* Countdown timer
* Rest timer
* Automatic rest timer
* Interval timer
* Lap timing
* Split timing
* Exercise duration
* Workout duration
* Timed sets
* Timed exercises
* HIIT intervals
* Walking intervals
* Running intervals
* Pause / resume
* Timer history

Timer information may eventually be stored with workout history.

This could allow analysis of:

* Workout duration
* Average rest time
* Exercise timing
* Session efficiency
* Interval performance

The stopwatch and timers may eventually be controlled through mobile and wearable devices.

---

# 8. Nutrition & Macro System

The platform should include structured nutrition tracking.

Potential features include:

* Daily calorie target
* Protein target
* Carbohydrate target
* Fat target
* Fiber target
* Macro tracking
* Food database
* Meal logging
* Meal planning
* Daily nutrition totals
* Weekly nutrition averages
* Meal recommendations
* Food substitutions
* Favorite meals
* Personalized meal ideas

---

## Food Database

Potential food information includes:

* Food ID
* Food name
* Serving size
* Calories
* Protein
* Carbohydrates
* Fat
* Fiber
* Sodium
* Other relevant nutrition information
* Ingredients
* Allergen information

Nutrition values should come from structured data sources wherever possible rather than being invented by an LLM.

---

## Allergy & Dietary Filtering

Before recommending food, the system should filter according to:

* Allergies
* Dietary restrictions
* Religious dietary preferences
* Foods avoided
* Foods disliked

Allergy checks should be handled using explicit software rules.

---

## Meal Personalization

Meal recommendations may consider:

* Nutrition target
* Macro target
* Foods the user likes
* Foods the user avoids
* Budget
* Cooking skill
* Cooking time
* Available ingredients
* Meal frequency
* Lifestyle

---

# 9. Personalized Recommendation System

The recommendation engine should connect user information with structured data.

Potential recommendations include:

* Exercise selection
* Workout split
* Workout frequency
* Training volume
* Sets
* Repetitions
* Exercise substitutions
* Progression strategies
* Recovery strategies
* Nutrition targets
* Macro targets
* Meal suggestions
* Activity recommendations

---

## Recommendation Inputs

Recommendations may consider:

* User goals
* Age
* Fitness level
* Training experience
* Available equipment
* Schedule
* Environment
* Exercise preferences
* Physical limitations
* Nutrition preferences
* Research evidence
* Workout history
* Nutrition history
* Activity history
* Progress
* Recovery
* Sleep

The recommendation system should initially use understandable rule-based logic.

Machine-learning methods may be explored later when enough meaningful data exists.

---

## Context-Aware Personalization

Recommendations should fit the user's real-world situation rather than generating generic plans.

For example, the system may consider:

* How many days the user can train
* How much time they have
* Whether they have gym access
* Whether they are travelling
* Whether they work a physically demanding job
* Whether they prefer outdoor activity
* What exercises they enjoy
* What food is available to them
* How much time they have for cooking

The system may adjust plans when circumstances change.

---

## Adaptive Planning

The long-term recommendation loop should work approximately as follows:

User Profile

↓

Initial Plan

↓

User Performs Activities

↓

Workout + Nutrition + Activity Data

↓

Progress Tracking

↓

Adherence Analysis

↓

Recovery Analysis

↓

Recommendation Adjustment

↓

Updated Plan

↓

Repeat

The goal is to create an adaptive system rather than a static plan generator.

---

# 10. Activity & Movement Tracking

The platform should eventually track daily activity.

Potential data includes:

* Steps
* Distance
* Walking speed
* Running speed
* Average speed
* Maximum speed
* Activity duration
* Activity type
* Stopwatch/activity timer data
* GPS route
* Map
* Elevation
* Daily activity
* Activity history
* Workout activity
* Phone activity data
* Wearable activity data

---

## GPS & Route Tracking

For activities such as:

* Walking
* Running
* Cycling
* Hiking

the application may eventually record:

* Route
* Distance
* Speed
* Duration
* Elevation
* Start point
* End point

Location tracking should always be optional.

Users should explicitly enable location-based features.

---

## Daily Energy & Activity Estimation

The system may estimate daily energy expenditure using available data.

Potential inputs include:

* User characteristics
* Daily activity
* Steps
* Distance
* Workouts
* Activity duration
* Wearable measurements
* Other supported activity information

The system should clearly distinguish:

* Measured values
* User-entered values
* Calculated values
* Estimated values

Calories burned should be presented as an estimate rather than an exact measurement.

Energy-expenditure estimates may be used as one input for nutrition recommendations.

---

# 11. Progress Tracking

Users should be able to track progress over time.

Potential data includes:

* Bodyweight
* Strength
* Exercise performance
* Training volume
* Workout consistency
* Nutrition consistency
* Calories
* Macros
* Steps
* Distance
* Activity
* Body measurements
* Personal records
* Progress photos

---

## Progress Photos

Users may optionally upload standardized progress photographs.

Potential features include:

* Front-view comparison
* Side-view comparison
* Back-view comparison
* Timeline comparison
* Photo organization
* Progress visualization

The application should encourage similar:

* Lighting
* Camera distance
* Camera position
* Pose
* Clothing
* Timing

when comparing photos.

Image analysis should focus on observable changes and progress toward user-selected goals.

It should not judge the user's attractiveness or claim to determine genetics from photographs.

Apparent asymmetry may be described cautiously but should not be presented as a medical diagnosis.

---

# 12. Calendar, Scheduling & History

The application should provide calendar-based tracking.

Potential features include:

* Planned workouts
* Completed workouts
* Missed workouts
* Rest days
* Activity sessions
* Meal planning
* Daily calories
* Daily macros
* Steps
* Distance
* Progress photos
* Weight
* Measurements
* Personal records
* Reminders
* Weekly summaries
* Monthly summaries
* Workout history
* Nutrition history
* Activity history

Calendar information should help users understand their consistency and long-term habits.

---

# 13. Analytics Dashboard

The platform should provide data-driven analytics.

---

## Training Analytics

Potential metrics include:

* Weekly training volume
* Muscle-group volume
* Strength progression
* Workout frequency
* Workout consistency
* Exercise performance
* Personal records
* Average workout duration
* Average rest periods

---

## Nutrition Analytics

Potential metrics include:

* Average calories
* Protein consistency
* Carbohydrate intake
* Fat intake
* Fiber intake
* Macro distribution
* Weekly averages
* Nutrition adherence

---

## Activity Analytics

Potential metrics include:

* Daily steps
* Weekly steps
* Distance
* Average speed
* Activity duration
* Active days
* Walking/running trends
* Estimated energy expenditure

---

## Progress Analytics

Potential metrics include:

* Weight trends
* Strength trends
* Workout consistency
* Nutrition consistency
* Activity trends
* Goal progress

The analytics system should use:

* Pandas
* Statistics
* SQL
* Data visualization
* Time-series analysis

where appropriate.

---

# 14. AI Assistant

The AI assistant should provide a natural-language interface to the platform.

Potential capabilities include:

* Answer fitness questions
* Answer nutrition questions
* Explain research
* Explain recommendations
* Explain exercises
* Suggest exercise alternatives
* Modify workout plans
* Suggest meals
* Explain macro targets
* Analyze tracked data
* Explain progress
* Explain trends
* Help users navigate the application

The AI should use structured user data and research evidence where appropriate.

It should not simply generate recommendations without context.

---

# 15. Retrieval-Augmented Generation

A future version will use Retrieval-Augmented Generation to connect the AI assistant to the curated research database.

Potential pipeline:

User Question

↓

Question Processing

↓

Research Retrieval

↓

Relevant Evidence

↓

Evidence Quality Information

↓

LLM Context

↓

Generated Explanation

↓

Sources / Citations

The system should be capable of communicating when evidence is:

* Strong
* Limited
* Mixed
* Conflicting
* Not directly applicable

The AI should not claim that a study proves something when the evidence does not support that level of certainty.

---

# 16. Computer Vision

A future version may include computer-vision capabilities.

Potential areas include:

* Progress photo comparison
* Pose estimation
* Exercise-form analysis
* Movement analysis
* Exercise technique feedback

---

## Exercise Form Analysis

Possible future pipeline:

Video / Image

↓

Pose Detection

↓

Body Landmarks

↓

Movement Tracking

↓

Joint / Position Analysis

↓

Technique Feedback

The system should not diagnose injuries based on images or videos.

---

# 17. Web & Mobile Applications

The platform should eventually be available across multiple devices.

---

## Web Application

Potential features include:

* Responsive interface
* Dashboard
* User profile
* Research library
* Workout tracking
* Nutrition tracking
* Activity tracking
* Calendar
* Analytics
* AI assistant

---

## iOS Application

Future possibilities include:

* Workout logging
* Nutrition logging
* Activity tracking
* AI assistant
* Camera integration
* Notifications
* GPS
* Wearable integration

---

## Android Application

Future possibilities include:

* Workout logging
* Nutrition logging
* Activity tracking
* AI assistant
* Camera integration
* Notifications
* GPS
* Wearable integration

---

## Shared Backend

The recommendation system, databases, research engine, and AI systems should be separated from the user interface.

The long-term architecture should allow:

Web

iOS

Android

Wearables

to communicate with the same core backend services.

---

# 18. Wearable Integration

A future version may integrate with supported wearable devices.

Potential data includes:

* Steps
* Heart rate
* Distance
* Activity
* Workout duration
* Exercise duration
* Timer information
* Estimated energy expenditure
* Sleep-related data
* Recovery-related metrics

Potential platforms include:

* Apple Watch
* Android / Google wearable ecosystem
* Other supported fitness devices

Wearable measurements should be treated according to their limitations.

Estimated values should not be presented as exact physiological measurements.

---

# 19. Privacy, Security & User Control

AI-Fitness may eventually handle sensitive information.

Potential sensitive data includes:

* Personal information
* Biometrics
* Fitness information
* Nutrition information
* Workout history
* Progress photos
* GPS/location data
* Wearable data
* Health-related information

The platform should follow privacy-first design principles.

---

## User Control

Users should control optional data collection.

Examples include:

* Location
* Progress photos
* Wearable information
* Health-related information

Users should be able to understand what data is being collected and why.

---

## Data Security

Future production versions should consider:

* Authentication
* Secure passwords
* Authorization
* Secure database access
* Encryption where appropriate
* Secrets management
* API security
* Secure photo storage
* Secure location-data storage
* Data deletion
* Account deletion
* Backup strategies

Sensitive credentials and API keys must never be committed to GitHub.

---

# 20. Safety & Responsible Recommendations

AI-Fitness should provide fitness information and general wellness guidance rather than pretending to replace qualified healthcare professionals.

Safety systems should account for:

* Pain
* Physical limitations
* Allergies
* Medical-risk situations
* Unusual symptoms
* Unsafe exercise requests
* Extreme nutrition requests

Nutrition recommendations should avoid pretending to diagnose or treat medical conditions.

Workout recommendations should not diagnose injuries.

The system should communicate uncertainty where appropriate.

---

# 21. System Architecture

The long-term architecture may approximately follow:

User

↓

Web / Mobile / Wearable Interface

↓

Authentication & User Profile

↓

Core Backend / API

↓

Fitness + Nutrition + Activity + Progress Data

↓

Recommendation Engine

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↙&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ↘

Structured Databases    /    Research Engine

↓                           ↓

Rules / Algorithms          Retrieval / RAG

↘             &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;            ↙

AI Assistant

↓

Safety & Validation Layer

↓

Personalized Recommendation

↓

User Feedback & New Data

↓

Adaptive Planning

The AI layer should support the application rather than control every system.

---

# 22. Testing & Evaluation

Testing should become an important part of the project.

Potential testing areas include:

* Unit tests
* Data validation
* Database tests
* Calculation tests
* Nutrition calculation tests
* Recommendation tests
* Allergy-filter tests
* Exercise-filter tests
* API tests
* AI response evaluation
* RAG retrieval evaluation
* Citation validation
* Safety testing
* User-interface testing

Important calculations should have predictable test cases.

AI recommendations should be evaluated rather than assumed to be correct.

---

# 23. Development Roadmap

## Stage 0 — Project Setup

Learn and implement:

* Git
* GitHub
* Repository creation
* PyCharm
* Project documentation
* Version control
* Commit workflow

**Status: COMPLETE**

---

## Stage 1 — Research Database

Learn:

* Scientific research organization
* Study designs
* Evidence quality
* Data extraction
* Data cleaning
* CSV
* JSON
* Pandas
* Research metadata
* Research licensing
* Citations
* Original research summaries

Build:

* Small curated research dataset
* Research schema
* Topic classification
* Evidence fields

---

## Stage 2 — Research Search & Retrieval Basics

Learn:

* Text processing
* Search
* Keywords
* TF-IDF
* Cosine similarity
* Information retrieval

Build a basic research-search system without using an LLM.

---

## Stage 3 — Database Fundamentals

Learn:

* SQL
* SQLite
* Tables
* Primary keys
* Foreign keys
* Relationships
* Normalization
* CRUD operations

Begin migrating structured project data from CSV files into databases where appropriate.

---

## Stage 4 — Exercise Database

Build:

* Exercise dataset
* Muscle groups
* Movement patterns
* Equipment
* Difficulty
* Exercise alternatives
* Exercise preferences

---

## Stage 5 — User Profile

Build:

* User data model
* Fitness profile
* Goals
* Preferences
* Limitations
* Biometrics
* Schedule
* Environment
* Lifestyle information

---

## Stage 6 — Nutrition System

Build:

* Food database
* Calories
* Macros
* Meal logging
* Nutrition targets
* Allergy filtering
* Food preferences

---

## Stage 7 — Rule-Based Recommendation Engine

Build the first recommendation system without depending on an LLM.

Implement:

* Exercise filtering
* Exercise recommendation
* Exercise substitution
* Workout generation
* User preferences
* Equipment constraints
* Schedule constraints
* Nutrition constraints

---

## Stage 8 — Workout Logging & Timer System

Build:

* Workout sessions
* Sets
* Repetitions
* Load
* Workout history
* Stopwatch
* Countdown timer
* Rest timer
* Interval timer
* Workout duration

---

## Stage 9 — Progress, Activity & Calendar Tracking

Build:

* Workout history
* Strength tracking
* Nutrition history
* Weight tracking
* Activity tracking
* Steps
* Distance
* Calendar
* Scheduling
* Progress data

---

## Stage 10 — Analytics

Learn and implement:

* Pandas analytics
* Statistics
* Time-series data
* Data visualization
* Training trends
* Nutrition trends
* Activity trends
* Progress trends

---

## Stage 11 — Backend, API & User Accounts

Learn:

* Backend architecture
* APIs
* Authentication
* Authorization
* Database access
* User accounts
* Security fundamentals

Create a shared backend that future web and mobile applications can use.

---

## Stage 12 — AI & RAG

Learn and implement:

* NLP
* Embeddings
* Vector databases
* Semantic search
* Retrieval
* Chunking
* Prompt construction
* LLM APIs
* RAG
* Research citations
* AI evaluation

Build a research-grounded fitness and nutrition assistant.

---

## Stage 13 — Adaptive Personalization

Combine:

* User history
* Workout history
* Nutrition history
* Activity
* Progress
* Preferences
* Research

to begin adapting recommendations over time.

---

## Stage 14 — Computer Vision

Learn:

* Image processing
* Computer vision
* Pose estimation
* Image comparison
* Video analysis

Explore:

* Progress-photo comparison
* Exercise-form analysis

---

## Stage 15 — Web Application

Build a full responsive user interface containing:

* Dashboard
* User profile
* Research system
* Workout system
* Nutrition system
* Activity tracking
* Calendar
* Analytics
* AI assistant

---

## Stage 16 — Mobile Applications

Explore:

* iOS
* Android
* Cross-platform development
* Notifications
* Camera
* GPS
* Mobile activity tracking

---

## Stage 17 — Wearable Integration

Explore:

* Apple Watch
* Android / Google wearables
* Fitness APIs
* Health/activity APIs
* Steps
* Heart rate
* Activity
* Timers
* Workout information

---

## Stage 18 — Testing, Deployment & Monitoring

Learn:

* Automated testing
* Deployment
* Logging
* Error monitoring
* Database backups
* API monitoring
* AI evaluation
* Performance testing
* Security testing

Prepare the platform for real users.

---

# 24. Development Philosophy

The project should be developed progressively.

The goal is not to ask AI to generate the entire application.

The preferred learning process is:

Understand the problem

↓

Design the data

↓

Research the concepts

↓

Attempt implementation

↓

Test the implementation

↓

Debug problems

↓

Review the solution

↓

Improve the design

↓

Commit meaningful progress to GitHub

AI tools may be used as:

* Tutors
* Debugging assistants
* Code reviewers
* Research assistants
* Explanation tools

They should not replace understanding of the underlying system.

---

# 25. Git & Documentation Strategy

Meaningful development stages should be documented with Git.

Typical workflow:

Make changes

↓

`git status`

↓

Review changes

↓

`git add`

↓

`git diff --cached`

↓

`git commit`

↓

`git push`

Commits should describe meaningful changes.

Documentation should evolve alongside the application.

Potential project documentation includes:

* `README.md`
* `PROJECT_PLAN.md`
* `RESEARCH_DATA_DESIGN.md`
* Database documentation
* Architecture documentation
* API documentation
* Testing documentation

---

# 26. Feature Scope Rule

This document represents the **long-term product vision**.

New feature ideas should not automatically interrupt the current development stage.

Future ideas can be recorded in:

* GitHub Issues
* Feature backlog
* Future roadmap documentation

The development priority should remain focused on the current stage until a usable milestone is completed.

This prevents the project from becoming permanently stuck in the planning phase.

---

# 27. Current Priority

The immediate priority is:

## Stage 1 — Research Database

Do not begin by building:

* The chatbot
* RAG
* Computer vision
* Mobile applications
* Watch integration
* GPS tracking
* The complete recommendation engine

The first technical objective is to learn how to:

1. Find appropriate research.
2. Understand research metadata.
3. Track licensing and attribution.
4. Structure research information.
5. Create original summaries.
6. Store research data.
7. Clean research data.
8. Analyze research data.
9. Search research data.
10. Prepare the research foundation for later retrieval and AI systems.

Once this foundation is understood and working, development can move to the next stage.

---

# Final Vision

The eventual AI-Fitness platform should connect:

Research

*

User Profile

*

Exercise Data

*

Nutrition Data

*

Workout History

*

Activity Data

*

Wearable Data

*

Progress Data

↓

Recommendation Engine

↓

AI / RAG

↓

Safety & Validation

↓

Personalized Fitness, Nutrition & Activity Guidance

↓

Tracking

↓

Progress Analysis

↓

Adaptive Recommendations

The final product should demonstrate not only AI capabilities but also strong skills in data science, software engineering, databases, recommendation systems, analytics, computer vision, privacy, and product development.
