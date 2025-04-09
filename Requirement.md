Transportation Management System Database Requirements
Project Overview
The company operates in the logistics sector, specializing in transporting goods between various locations. The proposed database system will track vehicles, drivers, maintenance records, load deliveries, and real-time vehicle status information. The application will implement a role-based access control system with differentiated viewing and editing permissions.
Business Requirements

Enable efficient tracking of the company's vehicle fleet
Maintain comprehensive driver information
Document all vehicle maintenance activities
Track load delivery operations from source to destination
Monitor real-time vehicle status and location information
Implement appropriate access controls based on user roles

Database Design
Entity Relationship Structure
The following tables constitute the core database design, with appropriate relationships to maintain data integrity across the system:
Vehicle Table

Vehicle_ID (Primary Key)
License_Plate (Unique identifier)
Make_Model
Year
DateOfPurchase
Acquisition_Cost
Current_Mileage
Fuel_Type
Capacity_Weight
Driver_ID (Foreign Key)

Driver Table

Driver_ID (Primary Key)
Driver_Name
Driver_ContactNumber
Driver_SSN
Driver_License_Number
License_Expiration_Date
Employment_Start_Date
Emergency_Contact
Address
Qualification_Details

Maintenance Table

Maintenance_ID (Primary Key)
Vehicle_ID (Foreign Key)
Maintenance_Type
Maintenance_Date
Cost
Service_Provider
Description
Next_Service_Date
Service_Status

Loads Table

Load_ID (Primary Key)
Vehicle_ID (Foreign Key)
Source
Destination
Scheduled_Departure
Scheduled_Arrival
Actual_Departure
Actual_Arrival
Customer_Name
Customer_Contact
Load_Description
Load_Weight
Delivery_Status
Special_Instructions

Status Table

Status_ID (Primary Key)
Vehicle_ID (Foreign Key)
Current_Location
Current_Status (Available, In-Transit, Under Maintenance, etc.)
Last_Updated
Fuel_Level
Estimated_Time_To_Destination
Next_Scheduled_Stop

Application Requirements
User Interface

The application will be developed using Python's Tkinter library
The interface will be intuitive, responsive, and aligned with the company's visual identity
The application will feature appropriate data visualization components for status monitoring

Role-Based Access Control

View-Only User

Can access a dashboard displaying all tables
Limited to executing SELECT statements only
Can generate reports and export data
Can filter and search across all tables
Cannot modify any data


Administrator User

Full access to all tables
Can execute SELECT, INSERT, UPDATE, and DELETE operations
Can modify vehicle details, maintenance records, and status information
Can assign drivers to vehicles
Can manage load assignments
Can generate comprehensive reports



Technical Requirements

Database: SQL Server/MySQL/PostgreSQL (to be determined)
Front-end: Python with Tkinter
Authentication: Secure login system with password encryption
Data Validation: Implementation of appropriate data validation rules
Backup: Automated database backup procedures
Logging: Activity logging for all database modifications

Functional Requirements

Real-time status updates of vehicle locations
Automated alerts for upcoming maintenance based on mileage or scheduled dates
Dashboard showing fleet utilization metrics
Report generation for fleet performance, maintenance costs, and delivery efficiency
Data export functionality for external analysis
Search and filter capabilities across all entities

Non-Functional Requirements

The system should support concurrent access by multiple users
Database transactions should complete within 3 seconds
The system should be available 99.9% of operating hours
All personal data must be encrypted in accordance with relevant data protection laws
The system should be scalable to accommodate growth in fleet size

Implementation Phases

Phase 1: Database design and normalization
Phase 2: Implementation of core database functionality
Phase 3: Development of view-only user interface
Phase 4: Development of administrator user interface
Phase 5: Testing and quality assurance
Phase 6: Deployment and user training

Constraints and Assumptions

The system will initially support up to 100 vehicles
The system will operate on the company's internal network
User authentication will integrate with existing company systems where possible

Deliverables

Fully normalized database schema
Working application with differentiated user interfaces
User documentation
Technical documentation including database diagram
Training materials for both user types

This requirements document provides a comprehensive framework for the development of the transportation management system database, addressing the core business needs while ensuring technical viability and future scalability.