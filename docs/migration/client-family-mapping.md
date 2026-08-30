# Client and Family Data Migration Mapping

## Overview
This document specifies how legacy single-table client attributes map cleanly to the normalized Phase 2 Person & Family schema without data loss.

## Field Mapping Matrix

| Legacy Field | Phase 2 Target Table | Phase 2 Column | Notes |
| :--- | :--- | :--- | :--- |
| `first_name` | `persons` & `clients` | `first_name` | Preserved on both for performance and canonical identity |
| `last_name` | `persons` & `clients` | `last_name` | Preserved on both |
| `date_of_birth` | `persons` & `clients` | `date_of_birth` | Stored as standard ISO date |
| `gender` | `persons` & `clients` | `gender` | Standardized gender |
| `status` | `clients` | `status` | Service status (Pending Intake, Active, Closed) |
| `risk_level` | `clients` | `risk_level` | Clinical risk tier |
| `phone` | `persons` & `person_contacts` | `phone` & `value` | Added to normalized contacts |
| `email` | `persons` & `person_contacts` | `email` & `value` | Added to normalized contacts |
| `address` | `person_addresses` | `address_line_1` | Stored as primary address record |
| `city` | `person_addresses` | `city` | City |
| `province` | `person_addresses` | `province` | Default: Saskatchewan |
| `postal_code` | `person_addresses` | `postal_code` | Postal code |
| `indigenous_identity` | `persons` & `clients` | `indigenous_identity` | Cultural identity |
| `band_nation` | `persons` & `clients` | `band_nation` | First Nation affiliation |
| `treaty_number` | `persons` | `treaty_number` | Protected identifier with field permission |
| `emergency_contact_name` | `persons` | `emergency_contact_name` | Primary emergency contact |
| `emergency_contact_phone`| `persons` | `emergency_contact_phone`| Emergency phone |
| `family_id` | `family_members` | `family_id` | Relational join record |
