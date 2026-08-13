# DESIGN & USER EXPERIENCE SPECIFICATION — SHELFIE

## 1. DESIGN PHILOSOPHY & PRINCIPLES

1. **Restrained Consumer Utility**: Shelfie is a tool for book lovers. The interface prioritizes clarity, legibility, and high-speed interaction over decorative animations, heavy gradients, or unnecessary charts.
2. **Transparent AI State**: Machine learning predictions are never presented as absolute truth. The UI explicitly communicates confidence and failure states across 5 granular categories.
3. **Optimized for One-Handed Review**: Reviewing scanned books requires minimal effort. High-confidence matches can be bulk-confirmed, while ambiguous items feature clear touch targets and rapid correction mechanisms (`POST /api/match/`).

---

## 2. NAVIGATION & SCREEN MAP

```
+-----------------------------------------------------------------------+
|                            APP NAVIGATION                             |
+------------------------------------+----------------------------------+
                                     |
                +--------------------+--------------------+
                v                                         v
    +-----------------------+                 +-----------------------+
    |  TAB 1: My Library    |                 |   TAB 2: Scan Shelf   |
    |  (GET /api/library/)  |                 |   (Camera / Upload)   |
    +-----------+-----------+                 +-----------+-----------+
                |                                         |
                |                                         v
                |                             +-----------------------+
                |                             |   Processing Screen   |
                |                             | (POST /api/analyze/)  |
                |                             +-----------+-----------+
                |                                         |
                |                                         v
                |                             +-----------------------+
                |                             |    Review Screen      |
                |                             | (5 Granular States)   |
                |                             +-----------+-----------+
                |                                         |
                +<========================================+ POST /api/library/
```

---

## 3. SCREEN SPECIFICATIONS

### 3.1 Screen 1: Library Screen (`LibraryScreen.tsx`)
- **Purpose**: Displays the user's saved personal book collection (backed by `GET /api/library/`).
- **Key Elements**:
  - **Header**: App title ("Shelfie"), book count badge ("42 Books"), and "Scan Bookshelf" primary CTA button.
  - **Search Bar**: Quick local filter by title or author.
  - **Book List**: Clean vertical list cards containing:
    - Title (bold, primary text)
    - Author (secondary text)
    - Added date ("Added Aug 13")
    - Action: Delete / Remove book.
  - **Empty State**: Rendered when library count is 0:
    - Clean book stack vector illustration
    - Headline: "No Books in Library Yet"
    - Body: "Take a photo of your bookshelf to automatically catalog your collection."
    - Primary CTA: "Scan Your First Bookshelf"

---

### 3.2 Screen 2: Scan / Camera Screen (`ScanScreen.tsx`)
- **Purpose**: Photo acquisition via device camera or file gallery picker.
- **Key Elements**:
  - Full-screen camera preview (or system photo picker trigger).
  - Overlay guidelines: "Position bookshelf upright in clear lighting".
  - Action buttons:
    - Shutter Button (take photo)
    - Gallery Picker Button ("Pick from Photos")

---

### 3.3 Screen 3: Processing Overlay (`ProcessingScreen.tsx`)
- **Purpose**: Provide real-time feedback during the `POST /api/analyze/` API pipeline execution.
- **Key Elements**:
  - Animated progress indicator.
  - Stage indicator labels:
    - `[✓]` Uploading bookshelf photo...
    - `[⚡]` Detecting book spines (Dynamic COCO lookup)...
    - `[🤖]` Transcribing titles & authors (Gemini 2.5 Flash)...
    - `[🔍]` Matching against canonical catalog...
  - Timing metadata display (e.g. `TBD — measured during benchmark phase`).

---

### 3.4 Screen 4: Results & Review Screen (`ReviewScreen.tsx`)
- **Purpose**: Human-in-the-loop review state displaying extracted crops categorized into 5 explicit states:

#### State 1: `matched` (High Confidence) — *Green Theme*
- Banner: "6 Books Auto-Matched" (Selected by default).
- Item Card: Spine crop thumbnail, matched catalog title & author, confidence score, checkbox toggle.

#### State 2: `needs_review` (Low Confidence / Ambiguous) — *Amber Theme*
- Banner: "2 Books Need Review" (Unchecked by default).
- Item Card: Spine crop thumbnail, raw VLM text, top candidate dropdown + option to rerun match (`POST /api/match/`) or select alternate.

#### State 3: `unmatched` (No Catalog Match Found) — *Gray Theme*
- Banner: "1 Unmatched Book".
- Item Card: Spine crop thumbnail, raw VLM text, "No catalog entry met match threshold". Actions: `Search Catalog` or `Type Manually`.

#### State 4: `unreadable` (Degraded / Illegible Text) — *Red Theme*
- Banner: "1 Unreadable Spine".
- Item Card: Spine crop thumbnail, "Text on spine is unreadable/degraded". Actions: `Search Catalog`, `Type Manually`, or `Discard`.

#### State 5: `extraction_failed` (VLM Timeout / Provider Error) — *Rose Theme*
- Banner: "1 Processing Error".
- Item Card: Spine crop thumbnail, "VLM request timed out or returned invalid format". Actions: `Retry Crop`, `Type Manually`, or `Discard`.

---

## 4. ERROR STATES & RECOVERY UX

| Failure State | Root Cause | Visual Feedback / UI Behavior | Recovery Action |
| :--- | :--- | :--- | :--- |
| **`zero_detected`** | No books found by local detector | Warning modal: "No book spines detected in photo." | Prompt user to retake photo with tighter framing. |
| **`extraction_failed`** | OpenRouter timeout or malformed JSON | Item tagged with red "Processing Error" badge. *(Not unreadable)* | "Retry Crop" button or manual tag entry. |
| **`unreadable`** | Worn/blurry physical spine text | Item tagged with amber "Unreadable Spine" badge. | Search catalog manually or type title/author. |
| **Upload Failure** | Network disconnected | Red alert banner: "Network Connection Failed". | "Retry Upload" button. |

---

## 5. DESIGN SYSTEM TOKENS

- **Primary / Brand**: Deep Indigo (`#2563EB`)
- **Background**: Neutral Off-White (`#F8FAFC`)
- **Card Background**: Pure White (`#FFFFFF`)
- **Text Primary**: Charcoal (`#0F172A`)
- **State `matched`**: Emerald (`#059669` / `#ECFDF5`)
- **State `needs_review`**: Amber (`#D97706` / `#FFFBEB`)
- **State `unmatched`**: Slate (`#64748B` / `#F1F5F9`)
- **State `unreadable`**: Rose (`#DC2626` / `#FEF2F2`)
- **State `extraction_failed`**: Purple (`#7C3AED` / `#F3E8FF`)
