## Pokémon Trade Inventory & Notification System

This project provides a web-based platform for managing a personal Pokémon inventory and receiving **real-time trade opportunity notifications** derived from posts in the Reddit community r/pokemontrades.

The system combines a **user inventory GUI**, a **fine-tuned large language model (LLM)** for parsing trade posts, and an **automated email notification pipeline** that alerts users when a trade opportunity matches their needs.

---

## Data Ingestion & Trade Detection Pipeline

The system continuously monitors new trade posts from the subreddit r/pokemontrades on Reddit and processes them through an automated pipeline that transforms unstructured post text into structured trade data and actionable notifications for users.

### 1. Post Ingestion

New submissions are retrieved from r/pokemontrades using the PRAW client, which interfaces with the Reddit API. The ingestion service periodically scans for newly published posts and forwards their titles and bodies into the parsing pipeline.

### 2. LLM Trade Parsing

Each Reddit post is passed to a **fine-tuned large language model** trained to extract structured Pokémon trade information from natural language posts.

The model converts free-form Reddit trade posts into structured JSON fields such as:

* offered Pokémon
* requested Pokémon
* IV values
* genders
* natures
* abilities
* forms
* languages
* special events (that is, Pokemon gained from specific events)
* Pokeballs caught in
* shiny status
* Pokemon game version
* type of post (trade, touch trade, giveaway, union circle, item trade, event, redeem or non-actionable)

This structured output follows the schema used throughout the system for representing Pokémon trades.

### 3. Trade Normalization

The parsed output is validated and normalized to ensure consistency with the internal schema used for user inventories and CSV exports. This allows downstream components to reliably compare trades and inventory data.

### 4. Inventory Matching

Parsed trade data is compared against user inventories stored in **AWS DynamoDB**. The system identifies when:

* a trade offers a Pokémon that a user **needs to complete their inventory**, or
* a user possesses a Pokémon that **fulfills the requirements of a posted trade**.

This matching process allows the platform to detect relevant opportunities for individual users.

### 5. Real-Time Email Notification

When a trade post matches a user’s inventory needs, the system generates a notification and sends a **real-time email alert** to subscribed users. The email includes information about the trade and a link to the original Reddit post so the user can quickly respond.

### 6. Continuous Monitoring

The ingestion and parsing pipeline runs continuously, enabling the system to surface trade opportunities shortly after they appear on r/pokemontrades.

---

This pipeline enables the platform to bridge **community-driven trade activity and structured data analysis**, allowing users to automatically discover trade opportunities that help complete their Pokémon collections.
