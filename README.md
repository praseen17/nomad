# NOMAD: The Modern Restaurant Operating System

![NOMAD Banner](static/images/image1.jpg)

"Run every table. Own every moment."

NOMAD is a multi-tenant, role-aware restaurant management platform designed with a high-end "Warm Brutalist Editorial" aesthetic. It manages everything from the moment a diner sits down to final billing, providing dedicated, real-time dashboards for Owners, Managers, Receptionists, Waiters, and Chefs.

## Current Project Status: Phase 2 (Active Development)

### ✅ Completed Milestones
- **Core Architecture & Models**: Full Django setup with multi-app architecture (`restaurant`, `workers`, `menu`, `tables`, `orders`, `billing`, `reviews`).
- **Visual Identity Engine**: Custom CSS framework (`nomad.css`) strictly enforcing the "Warm Brutalist" design language (Cormorant Garamond, Near-Black `#0E0C0A`, Terracotta `#D4622A` accents, micro-animations, custom cursor).
- **Authentication Gateway**: Multi-step owner registration, unified staff login using unique Worker IDs (e.g., `WTR-123456`), and a restricted Super Admin terminal.
- **Role Dashboards**: Specific live-data dashboards built for 5 distinct roles (Owner Analytics, Manager Floorplan, Reception Seating/Billing, Waiter Mobile Order Pad, Chef Contrast KDS).
- **Billing Logic Setup**: Subtotals, dynamic GST/discount math configured in the reception UI.
- **Firebase Initialization**: Environment variables securely loaded for Firebase integration.

### 🚧 Current WIP
- **Data Management (CRUD)**: Implementing the screens to allow owners to actively manage workers, tables, and the digital menu.
- **Multi-device Layout Adjustments**: Optimizing mobile views for waiter order pads and scaling logic for large-format Chef KDS screens.
- **Customer Interfaces**: Building the unauthenticated QR Digital Menu page and the post-billing review collection loop.

### 📅 Pending Enhancements
- **Live Integration**: Transitioning polling into actual WebSocket real-time updates via Django Channels (Phase 3).
- **Static File & Image Offloading**: Connecting Django models directly to the provided Firebase Storage bucket for dish/restaurant logos.
- **Generators**: PDF Invoice rendering and printable table-based QR code generation scripts.
- **VCS**: Continuous error-free GitHub deployment cycle.

---

## Tech Stack
- **Backend Framework**: Django 6.x (Python)
- **Frontend Architecture**: Vanilla HTML/CSS/JS (Server-rendered + Alpine.js planned for complex reactivity, replacing heavy SPA overheads to ensure speed on low-end restaurant hardware).
- **Database**: SQLite (Dev) -> PostgreSQL (Production ready).
- **Cloud Infrastructure**: Google Firebase (Storage, Analytics).
- **Styling**: Pure CSS Variables + Flex/Grid layouts (No Tailwind to ensure 100% adherence to specific brand tokens).

*Documentation continuously updated as platform evolves.*
