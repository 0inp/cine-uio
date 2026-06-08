# Architecture Deepening Plan for Cine-UIO

This document outlines actionable tasks to improve the architecture of the `cine-uio` codebase, ordered from **highest impact/easiest** to **lowest impact/hardest**. Each task includes:
- **Problem**: Why the current architecture is causing friction.
- **Solution**: Proposed changes.
- **Files**: Affected files.
- **Benefits**: Improvements in leverage, locality, and testability.

---

## **Frontend Tasks**

### **1. Extract `ScreeningService` for Data Fetching**
#### **Problem**
- `App.tsx` handles API calls directly, creating tight coupling and poor testability.

#### **Solution**
- Move data fetching into `services/ScreeningService.ts`.
- Use dependency injection for `fetch` (e.g., pass as a prop or use a context).

#### **Files**
- `/frontend/src/App.tsx`
- `/frontend/src/services/ScreeningService.ts` (new)

#### **Benefits**
- **Leverage**: Reusable across the app.
- **Locality**: API logic lives in one place.
- **Testability**: Easy to mock `fetch`.

---

### **2. Extract `useScreenings` Custom Hook**
#### **Problem**
- State management logic is embedded in `App.tsx`.

#### **Solution**
- Move state (e.g., `screenings`, `loading`, `error`) into `hooks/useScreenings.ts`.

#### **Files**
- `/frontend/src/App.tsx`
- `/frontend/src/hooks/useScreenings.ts` (new)

#### **Benefits**
- **Locality**: State logic lives in one place.
- **Testability**: Hooks can be unit-tested.

---

### **3. Extract UI Components**
#### **Problem**
- `App.tsx` renders all UI, making it hard to maintain.

#### **Solution**
- Split into `components/`:
  - `ScreeningList.tsx`
  - `ScreeningCard.tsx`
  - `MovieCard.tsx`

#### **Files**
- `/frontend/src/App.tsx`
- `/frontend/src/components/` (new)

#### **Benefits**
- **Leverage**: Reusable components.
- **Locality**: UI logic is isolated.

---

### **4. Add Runtime Validation for API Responses**
#### **Problem**
- No validation for API responses (e.g., malformed data).

#### **Solution**
- Use `zod` to validate responses in `ScreeningService.ts`.

#### **Files**
- `/frontend/src/services/ScreeningService.ts`

#### **Benefits**
- **Leverage**: Reusable validation.
- **Testability**: Easy to test error cases.

---

### **5. Extract Date Logic to `utils/date.ts`**
#### **Problem**
- Date filtering logic is embedded in `App.tsx`.

#### **Solution**
- Move to `utils/date.ts` (e.g., `filterScreeningsByDate`).

#### **Files**
- `/frontend/src/App.tsx`
- `/frontend/src/utils/date.ts` (new)

#### **Benefits**
- **Locality**: Date logic lives in one place.
- **Testability**: Pure functions can be unit-tested.

---

### **6. Improve Error Handling**
#### **Problem**
- Minimal error handling in `App.tsx`.

#### **Solution**
- Extract error handling into `utils/error.ts` (e.g., retry logic).

#### **Files**
- `/frontend/src/App.tsx`
- `/frontend/src/utils/error.ts` (new)

#### **Benefits**
- **Locality**: Error logic is centralized.

---

## **Backend Tasks**

### **1. Introduce a Service Layer (`services/screening.py`)**
#### **Problem**
- `api.py` mixes HTTP and business logic (e.g., converting models to schemas).

#### **Solution**
- Move logic to `services/screening.py`.

#### **Files**
- `/backend/app/api.py`
- `/backend/app/services/screening.py` (new)

#### **Benefits**
- **Leverage**: Reusable across routes.
- **Locality**: Business logic lives in one place.

---

### **2. Move Business Logic to `entities.py`**
#### **Problem**
- `entities.py` is just dataclasses with no behavior.

#### **Solution**
- Add methods for validation, transformations, and invariants.

#### **Files**
- `/backend/app/entities.py`

#### **Benefits**
- **Locality**: Business logic is centralized.
- **Testability**: Easy to unit-test.

---

### **3. Split `scraper.py` into `scraper/fetch.py` and `scraper/store.py`**
#### **Problem**
- Scraping logic is tightly coupled to the database.

#### **Solution**
- Split into:
  - `scraper/fetch.py`: Pure scraping logic.
  - `scraper/store.py`: Database operations.

#### **Files**
- `/backend/app/scraper.py`
- `/backend/app/scraper/fetch.py` (new)
- `/backend/app/scraper/store.py` (new)

#### **Benefits**
- **Leverage**: Reusable scraping logic.
- **Testability**: Easy to mock database.

---

### **4. Replace Global `SessionLocal()` with Dependency Injection**
#### **Problem**
- `database.py` uses a global session, creating implicit dependencies.

#### **Solution**
- Inject the database session explicitly.

#### **Files**
- `/backend/app/database.py`

#### **Benefits**
- **Testability**: Easy to mock.

---

### **5. Consolidate Validation Logic**
#### **Problem**
- Validation is split between `schemas.py` and `entities.py`.

#### **Solution**
- Move business validation to `entities.py`.

#### **Files**
- `/backend/app/schemas.py`
- `/backend/app/entities.py`

#### **Benefits**
- **Locality**: Validation logic lives in one place.

---

## **Top Priorities**
1. **Frontend**: Extract `ScreeningService` and move API URL to `config.ts`.
2. **Backend**: Introduce a service layer (`services/screening.py`).
3. **Frontend**: Extract `useScreenings` hook and UI components.
4. **Backend**: Move business logic to `entities.py`.
