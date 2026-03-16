## Pokémon Trade Inventory & Notification System

This project provides a web-based platform for managing a personal Pokémon inventory and receiving **real-time trade opportunity notifications** derived from posts in the Reddit community r/pokemontrades.

The system combines a **user inventory GUI**, a **fine-tuned large language model (LLM)** for parsing trade posts, and an **automated email notification pipeline** that alerts users when a trade opportunity matches their needs.

---

## Overview

Users log in via email to access a web interface where they can maintain a structured inventory of Pokémon they own. The interface allows users to specify attributes such as IV values, gender, abilities, forms, language, special event status, Pokéball type, and shiny status. Users can preview and export their inventory as a CSV formatted according to the schema used for LLM outputs that characterize Pokémon trades.

Inventory data is stored in **AWS DynamoDB** allow the system to persist user data and compare it against new trade posts as they appear.

---

## Real-Time Trade Detection Pipeline

The system continuously monitors new posts from **r/pokemontrades** and processes them through an automated pipeline:

1. **Post Collection**

   * New posts from r/pokemontrades are retrieved through the Reddit API via PRAW Python client.

2. **LLM Trade Parsing**

   * Each post is parsed using a **fine-tuned LLM** trained to extract structured trade information such as:

     * offered Pokémon
     * requested Pokémon
     * IVs
     * genders
     * natures
     * abilities
     * forms
     * language
     * special conditions
     * pokeballs caught in
     * shiny
     * type of post (trade, giveaway, touch trade, item trade, union circle, or non-actionable)

3. **Structured Trade Representation**

   * The LLM outputs a structured JSON representation of the trade offer.

4. **Inventory Matching**

   * The parsed trade is compared against user inventories stored in DynamoDB.
   * The system identifies:

     * Pokémon the user **needs to complete their inventory**
     * Pokémon the user **already owns that could fulfill the trade**

5. **Email Notification**

   * When a relevant match is detected, the system sends a **real-time email alert** to subscribed users notifying them of the trade opportunity.

---

## User Interface

The inventory GUI allows users to manage Pokémon data through a table interface where each row represents a Pokémon. Users can:

* mark ownership of a Pokémon
* enter IV values (0–31)
* select genders, natures, abilities, forms, languages, special events, and Pokéball type
* indicate shiny status

The interface includes the following actions:

* **Upload** – send the generated CSV to the backend for storage in DynamoDB
* **Export** – download the current inventory as a CSV
* **Preview** – view the generated CSV before exporting
* **Update** – synchronize the GUI inventory with the backend database
* **Clear** – reset all interface inputs

---

## Architecture

The system is composed of three primary components:

**Frontend**

* Inventory management GUI
* CSV generation and preview

**Backend API**

* Authentication
* Inventory management
* CSV ingestion and updates
* Trade matching logic

**Automation Pipeline**

* Reddit post ingestion
* Fine-tuned LLM trade parser
* Inventory matching engine
* Email notification service

---

## Purpose

This project bridges **community trade activity and structured data pipelines**, enabling automated detection of relevant Pokémon trades and helping collectors quickly identify opportunities to complete their inventories.
