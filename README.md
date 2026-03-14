# 🏥 Hospital Management System (HMS)
Hospital Management System with Django, PostgreSQL, Serverless Email Service

A hospital management system with doctor availability, patient booking, Google Calendar integration, and serverless email notifications.

## 📋 Features

- **Role-based Authentication** - Separate signup/login for Doctors and Patients
- **Doctor Dashboard** - Create and manage availability slots
- **Patient Dashboard** - View doctors and book available slots
- **Double-Booking Prevention** - Race condition handling ensures no overlapping bookings
- **Google Calendar Integration** - Automatic event creation on both calendars
- **Serverless Email Notifications** - Welcome emails and booking confirmations via AWS Lambda
- **Responsive UI** - Bootstrap-based clean interface

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 4.2, Python 3.9+ |
| Database | PostgreSQL |
| ORM | Django ORM |
| Authentication | Session-based with roles |
| Calendar API | Google Calendar API (OAuth2) |
| Email Service | AWS Lambda + Serverless Framework |
| Frontend | HTML, CSS |
| Local Testing | serverless-offline |

## 📹 Demo Video

**Demo Video Link** - https://drive.google.com/file/d/1B5m9G4DYtKKJfyC1mO7pbNwx0Qst4yrQ/view?usp=sharing
