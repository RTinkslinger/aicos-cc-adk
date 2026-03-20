# shadcn/ui Component Composition Plan for AI CoS WebFront

> Research date: 2026-03-20
> Target: Transform digest.wiki from a content site into a world-class app (Linear / Superhuman / Arc tier)
> Stack: Next.js 16, React 19, Tailwind CSS v4, shadcn/ui (latest)

---

## Table of Contents

1. [Full Component Inventory](#1-full-component-inventory)
2. [Components We Need (Prioritised)](#2-components-we-need-prioritised)
3. [Page-by-Page Composition Plan](#3-page-by-page-composition-plan)
4. [Interaction Patterns](#4-interaction-patterns)
5. [Key Code Snippets](#5-key-code-snippets)
6. [Design Tokens & Typography](#6-design-tokens--typography)
7. [Migration Strategy](#7-migration-strategy)

---

## 1. Full Component Inventory

shadcn/ui ships ~59 components as of March 2026. Seven new ones (Spinner, Kbd, ButtonGroup, InputGroup, Field, Item, Empty) were added in October 2025. Below is every component, categorised by role with notes on our usage.

### Layout & Structure

| Component | What It Does | Our Use |
|-----------|-------------|---------|
| **Card** | Container with header/content/footer slots | Action cards, thesis cards, digest cards |
| **Separator** | Horizontal/vertical dividers | Section breaks, sidebar separators |
| **Resizable** | Draggable split-pane panels (react-resizable-panels) | Desktop: list + detail split view |
| **ScrollArea** | Custom-styled scrollable region | Action list, thesis list, evidence trail |
| **Collapsible** | Expand/collapse sections (Radix) | Evidence sections, reasoning expansion |
| **Aspect Ratio** | Constrained aspect ratio container | Not needed (no media) |
| **Sidebar** | Full sidebar with collapsible groups, tooltips | Main app navigation (desktop) |

### Navigation

| Component | What It Does | Our Use |
|-----------|-------------|---------|
| **NavigationMenu** | Horizontal nav with dropdown submenus | Not needed -- using Sidebar + mobile tabs |
| **Breadcrumb** | Path trail with separators | Thesis > Detail, Action > Detail breadcrumbs |
| **Tabs** | Tabbed content switching | Thesis: Evidence For/Against/Questions tabs; Actions: status view switching |
| **Pagination** | Page navigation controls | Action list pagination (if needed) |

### Overlays & Modals

| Component | What It Does | Our Use |
|-----------|-------------|---------|
| **Command** | cmdk-powered search + command palette | Global Cmd+K palette for navigation + actions |
| **Dialog** | Centered modal overlay | Quick action confirmation, keyboard shortcut help |
| **Sheet** | Slide-out panel (any side) | Action detail panel (right), thesis detail panel |
| **Drawer** | Mobile bottom drawer (Vaul, swipe-aware) | Mobile: action detail, thesis detail, filters |
| **Popover** | Floating content attached to trigger | Filter dropdowns, quick metadata preview |
| **HoverCard** | Rich preview on hover | Thesis thread preview, company preview, person preview |
| **Tooltip** | Small text on hover | Keyboard shortcut hints, score explanations |
| **ContextMenu** | Right-click menu | Power-user: right-click on action card |
| **AlertDialog** | Confirmation dialog | Batch dismiss confirmation |

### Data Display

| Component | What It Does | Our Use |
|-----------|-------------|---------|
| **Badge** | Small status/label indicator | Priority badges (P0-P3), status badges, conviction labels |
| **Progress** | Horizontal bar indicator | Conviction gauge alternative, relevance score bar |
| **Skeleton** | Loading placeholder | All data-loading states |
| **Table** | Styled HTML table | Compact action list view, data views |
| **Avatar** | Circular image/initials | Person avatars in network, assigned-to display |
| **Carousel** | Swipeable card container | Mobile: action triage card stack |
| **Empty** | Empty state with icon + message | Zero-state for each section |
| **Item** | List item display | Action list items, thesis list items |
| **Chart** | Recharts wrapper | Conviction history, action stats over time |
| **Typography** | Styled text primitives | Headings, prose sections |
| **Kbd** | Keyboard key display | Shortcut hints throughout UI |

### Forms & Input

| Component | What It Does | Our Use |
|-----------|-------------|---------|
| **Button** | Styled button with variants | Accept/Dismiss/Defer actions, all CTAs |
| **ButtonGroup** | Grouped buttons (split button pattern) | Triage button group (Accept | Dismiss | Defer) |
| **Toggle** | Two-state toggle button | View switching (card/table), feature toggles |
| **ToggleGroup** | Exclusive/multi toggle set | View mode: Card / List / Table; Thesis: For/Against/All |
| **Select** | Styled dropdown select | Filter dropdowns (priority, status, type) |
| **Checkbox** | Styled checkbox | Batch selection on action cards |
| **Switch** | Toggle switch | Settings toggles (keyboard mode, compact view) |
| **Input** | Styled text input | Search, command palette input |
| **InputGroup** | Input with icons/addons | Search with icon, filter with kbd hint |
| **Field** | Form field with label + error | Any edit forms |
| **Label** | Accessible label | Paired with all form elements |
| **Textarea** | Multi-line input | Notes, feedback forms |
| **Slider** | Numeric range slider | Not needed currently |
| **RadioGroup** | Exclusive radio options | Not needed currently |
| **Calendar** | Date picker calendar | Not needed currently |
| **DatePicker** | Calendar + popover input | Not needed currently |
| **InputOTP** | One-time password input | Not needed |
| **Form** | React Hook Form integration | Not needed currently |
| **Combobox** | Searchable select (Popover + Command) | Thesis filter, company filter |
| **NativeSelect** | Unstyled native select | Mobile fallback for selects |

### Feedback

| Component | What It Does | Our Use |
|-----------|-------------|---------|
| **Sonner** | Modern toast notifications (by Emil Kowalski) | Undo triage, batch results, success/error feedback |
| **Toast** | Older toast pattern (Radix) | Not needed -- Sonner is superior |
| **Alert** | Inline alert banner | System notices, pipeline status |
| **Spinner** | Loading indicator | Inline loading states |

### Menu

| Component | What It Does | Our Use |
|-----------|-------------|---------|
| **DropdownMenu** | Floating action menu | Card "..." menu, bulk actions dropdown |
| **Menubar** | Horizontal menu with dropdowns | Not needed |

---

## 2. Components We Need (Prioritised)

### Tier 1 -- Core App Shell (install first)

These create the fundamental app-like feel:

1. **Command** -- Global Cmd+K palette. The single most impactful "this feels like an app" component.
2. **Sonner** -- Toast with undo actions. Replaces the hand-built undo toast in ActionDetailTriage.
3. **Sidebar** -- Desktop navigation. Replaces the simple fixed top nav.
4. **Sheet** -- Detail panels sliding in from the right. Replaces full-page navigation for quick views.
5. **Drawer** -- Mobile-specific bottom drawer. Replaces Sheet on small screens.
6. **Kbd** -- Keyboard shortcut display throughout the UI.
7. **Skeleton** -- Loading states for every data section.

### Tier 2 -- Enhanced Data Display

8. **Badge** -- Replace hand-styled priority/status spans.
9. **Card** -- Standardise card containers across actions, thesis, digests.
10. **Tabs** -- Evidence for/against toggle, view switching on lists.
11. **ToggleGroup** -- View mode switching (card/list), status filter quick-toggle.
12. **ScrollArea** -- Custom-scrolling action/thesis lists.
13. **HoverCard** -- Entity preview on hover (thesis, company, person).
14. **Tooltip** -- Keyboard hints, score explanations.
15. **Progress** -- Conviction gauge, relevance score bar.
16. **Collapsible** -- Evidence sections, reasoning expansion.

### Tier 3 -- Power Features

17. **Resizable** -- Desktop split-pane (list + detail).
18. **DropdownMenu** -- Per-card action menus.
19. **ButtonGroup** -- Triage button cluster.
20. **Carousel** -- Mobile swipe-through action triage.
21. **Breadcrumb** -- Navigation path in detail views.
22. **Select** / **Combobox** -- Filter dropdowns.
23. **Avatar** -- Person/company display.
24. **Empty** -- Zero-state displays.
25. **Table** -- Compact data view mode.
26. **ContextMenu** -- Right-click on cards (power users).

---

## 3. Page-by-Page Composition Plan

### 3.1 App Shell (layout.tsx)

The fundamental shift: move from a simple top nav + centered content to a sidebar-driven app shell.

```
+--+-------------------------------+
|  |  Breadcrumb       [Cmd+K] [?]|
|S |-------------------------------|
|I |                               |
|D |     CONTENT AREA              |
|E |     (page-specific)           |
|B |                               |
|A |                               |
|R |-------------------------------|
|  |  Status bar (optional)        |
+--+-------------------------------+
```

**Desktop (>= 1024px):**
- `Sidebar` (left, collapsible): Logo, nav items (Digests, Actions, Thesis), plus secondary items
- `SidebarInset` wraps page content
- Top bar: `Breadcrumb` (left) + `Command` trigger button with `Kbd` hint (right)
- `Sonner` `<Toaster />` in layout root

**Tablet (768-1023px):**
- Sidebar collapses to icon-only rail
- Same content area, narrower

**Mobile (< 768px):**
- No sidebar -- bottom tab bar (custom, 4 tabs: Home, Actions, Thesis, Search)
- Top bar: page title + action button
- `Drawer` for detail views and filters
- `Command` accessible via search tab or swipe-down gesture

**Component composition:**
```tsx
<SidebarProvider>
  <Sidebar collapsible="icon">
    <SidebarHeader>
      {/* Logo + workspace switcher */}
    </SidebarHeader>
    <SidebarContent>
      <NavMain items={navigationItems} />
    </SidebarContent>
    <SidebarFooter>
      {/* Settings, keyboard shortcut help */}
    </SidebarFooter>
  </Sidebar>
  <SidebarInset>
    <header>
      <SidebarTrigger />
      <Breadcrumb>{/* dynamic */}</Breadcrumb>
      <CommandTrigger /> {/* Cmd+K button with Kbd display */}
    </header>
    <main>{children}</main>
    <Toaster /> {/* Sonner */}
  </SidebarInset>
</SidebarProvider>
```

### 3.2 Home Dashboard (/)

Current: Vertical scroll of stats + recent items.
Target: Dense, glanceable command center.

**Layout:**
```
+----------------------------------------+
|  Stats Grid (4 cards)                  |
|  [Pending] [Accepted] [Thesis] [Digests]|
+----------------------------------------+
|  [Tab: Recent Actions | Active Thesis | New Digests] |
+----------------------------------------+
|  Scrollable list based on active tab    |
|  Each item: Card with HoverCard preview |
|                                         |
+----------------------------------------+
```

**Components used:**
- `Card` -- Each stat block is a Card with a large number + label
- `Tabs` + `TabsList` + `TabsTrigger` + `TabsContent` -- Switch between recent actions, active thesis, new digests
- `ScrollArea` -- Scrollable list inside each tab
- `HoverCard` -- Hover over any action or thesis to see a preview without navigating
- `Badge` -- Priority/status/conviction inline badges
- `Skeleton` -- Loading placeholders for all data sections
- `Empty` -- Zero-state when no items in a tab

### 3.3 Action Triage (/actions)

This is the power page. The goal: Superhuman-level triage speed.

**Desktop Layout:**
```
+------------------+----------------------+
|  Filter bar      |                      |
|  [Status][Prio]  |                      |
|  [Type][Assign]  |                      |
+------------------+   DETAIL PANEL       |
|  Action List     |   (Sheet or inline)  |
|  (ScrollArea)    |                      |
|  [Card]          |   Reasoning          |
|  [Card] <active> |   Thesis connection  |
|  [Card]          |   Related digests    |
|  [Card]          |   Triage controls    |
|                  |                      |
+------------------+----------------------+
|  [Batch bar when items selected]        |
+------------------------------------------+
```

**Option A -- Resizable Split Pane (recommended for desktop):**
```tsx
<ResizablePanelGroup orientation="horizontal">
  <ResizablePanel defaultSize="40%" minSize="30%">
    {/* Filter bar + ScrollArea of action cards */}
  </ResizablePanel>
  <ResizableHandle withHandle />
  <ResizablePanel defaultSize="60%">
    {/* Selected action detail */}
  </ResizablePanel>
</ResizablePanelGroup>
```

**Option B -- Sheet Detail Panel:**
- Click a card -> `Sheet` slides in from right with full action detail
- Sheet stays open while navigating list with j/k keys
- Sheet content updates to match selected card

**Mobile Layout:**
- Full-screen scrollable list of action `Card` components
- Tap card -> `Drawer` slides up from bottom with detail + triage controls
- Swipe left on card = dismiss, swipe right = accept (gesture shortcut)
- `Carousel` mode: toggle to card-stack triage (one card at a time, swipe to decide)

**Components used:**
- `Card` -- Action cards with `Badge` for priority and status
- `ScrollArea` -- Action list with custom scrollbar
- `Resizable` (desktop) -- Split view: list + detail
- `Sheet` (desktop alt) or `Drawer` (mobile) -- Detail panel
- `ButtonGroup` -- Accept | Dismiss | Defer cluster
- `Sonner` -- "Action accepted. Undo" toast with action button
- `Checkbox` (inside cards) -- Batch selection
- `Select` or `Combobox` -- Filter dropdowns (replace current native selects)
- `ToggleGroup` -- Quick status filter: All | Proposed | Accepted | Dismissed
- `DropdownMenu` -- Per-card "..." menu (defer, change priority, assign, link thesis)
- `Tooltip` + `Kbd` -- "Press `a` to accept, `d` to dismiss"
- `Skeleton` -- Card-shaped loading states
- `Empty` -- "No actions match these filters. Try adjusting." with helpful message

**Triage Card Design:**
```tsx
<Card className="group relative">
  <CardHeader className="pb-2">
    <div className="flex items-center gap-2">
      <Badge variant="priority-p0">P0</Badge>
      <Badge variant="outline">Research</Badge>
      <Badge variant="status-proposed" className="ml-auto">Proposed</Badge>
    </div>
  </CardHeader>
  <CardContent>
    <CardTitle className="text-[15px]">{action.action}</CardTitle>
    <Collapsible>
      <CollapsibleTrigger>Show reasoning</CollapsibleTrigger>
      <CollapsibleContent>{action.reasoning}</CollapsibleContent>
    </Collapsible>
  </CardContent>
  <CardFooter>
    <ButtonGroup>
      <Button variant="accept">Accept</Button>
      <Button variant="dismiss">Dismiss</Button>
      <Button variant="defer">Defer</Button>
    </ButtonGroup>
  </CardFooter>
</Card>
```

### 3.4 Thesis Dashboard (/thesis)

**Desktop Layout:**
```
+----------------------------------------+
|  View toggle: [Cards] [Table]          |
|  Filter: [All] [Active] [Exploring]    |
+----------------------------------------+
|  Thesis Grid (2 columns)               |
|  +----------------+ +----------------+ |
|  | Card           | | Card           | |
|  | Conviction bar | | Conviction bar | |
|  | Evidence dots  | | Evidence dots  | |
|  +----------------+ +----------------+ |
|  +----------------+ +----------------+ |
|  | Card           | | Card           | |
|  +----------------+ +----------------+ |
+----------------------------------------+
```

**Thesis Card Design:**
```tsx
<Card>
  <CardHeader>
    <CardTitle>{thread.thread_name}</CardTitle>
    <div className="flex gap-2">
      <Badge variant="status">{thread.status}</Badge>
      {buckets.map(b => <Badge variant="outline" key={b}>{b}</Badge>)}
    </div>
  </CardHeader>
  <CardContent>
    {/* Conviction Gauge -- custom component wrapping Progress */}
    <ConvictionGauge level={thread.conviction} />
    <p className="text-sm text-muted-foreground line-clamp-3">
      {thread.core_thesis}
    </p>
  </CardContent>
  <CardFooter>
    <div className="flex gap-3 text-xs font-mono">
      <span className="text-green">{forCount} for</span>
      <span className="text-flame">{againstCount} against</span>
    </div>
  </CardFooter>
</Card>
```

**Thesis Detail View (/thesis/[id]):**

Instead of full-page navigation, use `Sheet` (desktop) or `Drawer` (mobile):

```
Sheet (from right, wide):
+------------------------------------------+
|  [X] Thread Name                         |
|  [Active] [AI Infra] [Developer Tools]   |
|------------------------------------------+
|  Conviction Gauge (full width)           |
|------------------------------------------+
|  Tabs: [Core] [Evidence] [Analysis] [Intel]|
|------------------------------------------+
|  Tab Content (ScrollArea)                |
|  - Core: thesis text + implications      |
|  - Evidence: For/Against with Collapsible|
|  - Analysis: Adversarial lens cards      |
|  - Intel: Companies, People, Digests     |
+------------------------------------------+
```

**Components used:**
- `Card` -- Thesis cards
- `Progress` (custom-styled) -- Conviction gauge bars
- `Badge` -- Status, conviction level, connected buckets
- `Tabs` -- Section switching in detail view
- `Collapsible` -- Evidence sections (show 3, expand to show all)
- `HoverCard` -- Preview thesis on hover in other pages
- `Sheet` (desktop) or `Drawer` (mobile) -- Detail view
- `ScrollArea` -- Detail panel content
- `ToggleGroup` -- View mode + status filter
- `Table` -- Alternative compact view of all thesis threads
- `Tooltip` -- Explain conviction levels, IDS notation

### 3.5 Digest Detail (/d/[slug])

Digests are the read-heavy page -- less interactivity needed, more focus on readability.

**Components used:**
- `Breadcrumb` -- "Digests > Channel > Title"
- `Badge` -- Relevance score, content type
- `Card` -- Sections (core arguments, contra signals, actions)
- `Collapsible` -- Expandable detailed sections
- `HoverCard` -- Thesis thread preview when mentioned
- `Tooltip` -- Score explanations
- `Separator` -- Between major sections
- `ScrollArea` -- Sidebar TOC on desktop (optional)

### 3.6 Global Command Palette

The single most important feature for app-like feel. Accessible from anywhere via Cmd+K.

**Structure:**
```
+------------------------------------------+
|  [Search icon] Type to search...    [Esc]|
|------------------------------------------+
|  Recent                                  |
|  > Last viewed thesis thread             |
|  > Last triaged action                   |
|------------------------------------------+
|  Actions            (type "action" to filter)|
|  > "Deep-dive on NVIDIA moat"        [P0]|
|  > "Schedule call with founder X"    [P1]|
|------------------------------------------+
|  Thesis Threads     (type "thesis")      |
|  > "AI Infrastructure Thesis"   [Active] |
|  > "Developer Tools Thesis"  [Exploring] |
|------------------------------------------+
|  Navigation         (type "go to")       |
|  > Go to Actions               [G] [A]  |
|  > Go to Thesis                [G] [T]  |
|  > Go to Digests               [G] [D]  |
|------------------------------------------+
|  Commands           (type "triage")      |
|  > Accept selected action          [A]   |
|  > Dismiss selected action         [D]   |
|  > Defer selected action           [F]   |
|  > Toggle keyboard mode         [Shift+?]|
+------------------------------------------+
```

---

## 4. Interaction Patterns

### 4.1 Keyboard Shortcuts (Superhuman-inspired)

The keyboard system follows Superhuman's philosophy: single-key shortcuts for frequent actions, modifier keys for less common ones.

#### Global Shortcuts

| Key | Action | Context |
|-----|--------|---------|
| `Cmd+K` | Open command palette | Everywhere |
| `G` then `A` | Go to Actions | Everywhere |
| `G` then `T` | Go to Thesis | Everywhere |
| `G` then `D` | Go to Digests | Everywhere |
| `G` then `H` | Go to Home | Everywhere |
| `?` | Show keyboard shortcut help (Dialog) | Everywhere |
| `Esc` | Close overlay / deselect | Everywhere |

#### Action Triage Shortcuts

| Key | Action | Context |
|-----|--------|---------|
| `J` | Next action (move down) | Action list |
| `K` | Previous action (move up) | Action list |
| `Enter` | Open detail panel | Action selected |
| `A` | Accept action | Action selected |
| `D` | Dismiss action | Action selected |
| `F` | Defer action | Action selected |
| `Z` | Undo last triage | After triage |
| `X` | Toggle batch selection | Action selected |
| `Shift+A` | Accept all selected | Batch mode |
| `Shift+D` | Dismiss all selected | Batch mode |
| `/` | Focus search/filter | Action list |
| `1`-`4` | Quick filter: P0, P1, P2, P3 | Action list |

#### Thesis Shortcuts

| Key | Action | Context |
|-----|--------|---------|
| `J` / `K` | Navigate thesis cards | Thesis list |
| `Enter` | Open thesis detail | Thesis selected |
| `E` | Toggle evidence view | Thesis detail |
| `Tab` | Next section tab | Thesis detail |
| `Shift+Tab` | Previous section tab | Thesis detail |

#### Implementation Pattern

```tsx
// useKeyboardShortcuts.ts -- global hook
import { useEffect, useCallback } from "react";

type ShortcutMap = Record<string, () => void>;

export function useKeyboardShortcuts(shortcuts: ShortcutMap) {
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Skip if user is typing in an input/textarea
    if (e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement) return;

    // Skip if Command palette is open
    if (document.querySelector("[cmdk-dialog]")) return;

    const key = [
      e.metaKey && "meta",
      e.shiftKey && "shift",
      e.key.toLowerCase(),
    ].filter(Boolean).join("+");

    shortcuts[key]?.();
  }, [shortcuts]);

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);
}
```

### 4.2 Undo Pattern (Sonner)

Replace the hand-built undo toast with Sonner's built-in action pattern:

```tsx
import { toast } from "sonner";

function handleTriage(decision: "Accepted" | "Dismissed") {
  // Optimistic UI update
  setOptimisticStatus(decision);

  // Show undo toast -- action executes after timeout if not undone
  toast(`Action ${decision.toLowerCase()}`, {
    description: action.action.slice(0, 60) + "...",
    action: {
      label: "Undo",
      onClick: () => {
        setOptimisticStatus("Proposed");
        // No server call needed -- we haven't committed yet
      },
    },
    duration: 5000,
    onAutoClose: () => {
      // Commit to server only when toast auto-closes (not undone)
      commitTriage(decision);
    },
  });
}
```

### 4.3 Responsive Dialog/Drawer Pattern

Desktop shows a Dialog or Sheet; mobile shows a Drawer. This is the standard shadcn pattern:

```tsx
import { useMediaQuery } from "@/hooks/use-media-query";

function ActionDetail({ action }: { action: ActionRow }) {
  const isDesktop = useMediaQuery("(min-width: 768px)");

  if (isDesktop) {
    return (
      <Sheet>
        <SheetContent side="right" className="w-[500px] sm:w-[600px]">
          <SheetHeader>
            <SheetTitle>{action.action}</SheetTitle>
          </SheetHeader>
          <ScrollArea className="h-[calc(100vh-120px)]">
            <ActionDetailContent action={action} />
          </ScrollArea>
          <SheetFooter>
            <TriageButtonGroup action={action} />
          </SheetFooter>
        </SheetContent>
      </Sheet>
    );
  }

  return (
    <Drawer>
      <DrawerContent>
        <DrawerHeader>
          <DrawerTitle>{action.action}</DrawerTitle>
        </DrawerHeader>
        <ScrollArea className="max-h-[60vh]">
          <ActionDetailContent action={action} />
        </ScrollArea>
        <DrawerFooter>
          <TriageButtonGroup action={action} />
          <DrawerClose asChild>
            <Button variant="outline">Close</Button>
          </DrawerClose>
        </DrawerFooter>
      </DrawerContent>
    </Drawer>
  );
}
```

### 4.4 Focus Management

Every interaction should feel instant and never lose the user's place:

- **J/K navigation**: Active card gets a visible ring (`ring-2 ring-flame/50`), the list scrolls to keep it visible.
- **Triage action**: After accepting/dismissing, focus auto-advances to next card (Superhuman's J behavior).
- **Sheet/Drawer close**: Focus returns to the card that triggered it.
- **Command palette close**: Focus returns to previous element.
- **Batch mode**: Checkbox selection preserves scroll position.

### 4.5 Transitions & Motion

One high-impact animation moment per interaction -- not scattered micro-interactions:

| Interaction | Animation | CSS Property |
|-------------|-----------|-------------|
| Card triage (accept) | Card slides right + fades | `transform: translateX()`, `opacity` |
| Card triage (dismiss) | Card slides left + fades | `transform: translateX()`, `opacity` |
| Sheet open | Slide from right | `transform: translateX()` |
| Drawer open | Slide from bottom | `transform: translateY()` |
| Command palette | Fade + scale in | `opacity`, `transform: scale()` |
| Toast appear | Slide up from bottom-right | `transform: translateY()` |
| Tab switch | Crossfade content | `opacity` |
| Focus ring | Smooth ring expansion | `box-shadow` transition |

All animations use `transform` and `opacity` only -- never layout properties.

### 4.6 Mobile Gestures

| Gesture | Action | Component |
|---------|--------|-----------|
| Swipe down from top | Open command palette | Custom hook |
| Swipe left on card | Quick dismiss | Custom + Sonner undo |
| Swipe right on card | Quick accept | Custom + Sonner undo |
| Swipe down on Drawer | Close drawer | Built into Vaul/Drawer |
| Long press on card | Open context menu | ContextMenu or DropdownMenu |
| Pull to refresh | Reload data | Custom hook + Spinner |

---

## 5. Key Code Snippets

### 5.1 Command Palette (Global Search + Navigation)

```tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command";
import { Kbd, KbdGroup } from "@/components/ui/kbd";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <Command>
        <CommandInput placeholder="Search actions, thesis, digests..." />
        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>

          <CommandGroup heading="Navigation">
            <CommandItem onSelect={() => { router.push("/"); setOpen(false); }}>
              Home Dashboard
              <CommandShortcut><KbdGroup><Kbd>G</Kbd><Kbd>H</Kbd></KbdGroup></CommandShortcut>
            </CommandItem>
            <CommandItem onSelect={() => { router.push("/actions"); setOpen(false); }}>
              Actions Queue
              <CommandShortcut><KbdGroup><Kbd>G</Kbd><Kbd>A</Kbd></KbdGroup></CommandShortcut>
            </CommandItem>
            <CommandItem onSelect={() => { router.push("/thesis"); setOpen(false); }}>
              Thesis Threads
              <CommandShortcut><KbdGroup><Kbd>G</Kbd><Kbd>T</Kbd></KbdGroup></CommandShortcut>
            </CommandItem>
          </CommandGroup>

          <CommandSeparator />

          {/* Dynamic: populated from Supabase queries */}
          <CommandGroup heading="Pending Actions">
            {/* Map over pending actions */}
          </CommandGroup>

          <CommandSeparator />

          <CommandGroup heading="Active Thesis">
            {/* Map over active thesis threads */}
          </CommandGroup>

          <CommandSeparator />

          <CommandGroup heading="Commands">
            <CommandItem>
              Accept selected action
              <CommandShortcut><Kbd>A</Kbd></CommandShortcut>
            </CommandItem>
            <CommandItem>
              Dismiss selected action
              <CommandShortcut><Kbd>D</Kbd></CommandShortcut>
            </CommandItem>
            <CommandItem>
              Show keyboard shortcuts
              <CommandShortcut><Kbd>?</Kbd></CommandShortcut>
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </Command>
    </CommandDialog>
  );
}
```

### 5.2 Conviction Gauge (Custom Component Using Progress)

```tsx
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const CONVICTION_STEPS = ["New", "Evolving", "Evolving Fast", "Low", "Medium", "High"];

function convictionToPercent(level: string | null): number {
  const idx = CONVICTION_STEPS.indexOf(level ?? "New");
  return idx === -1 ? 0 : ((idx + 1) / CONVICTION_STEPS.length) * 100;
}

function convictionColor(level: string | null): string {
  const idx = CONVICTION_STEPS.indexOf(level ?? "New");
  if (idx <= 1) return "var(--color-cyan)";
  if (idx <= 3) return "var(--color-amber)";
  return "var(--color-green)";
}

export function ConvictionGauge({
  level,
  variant = "bar",
}: {
  level: string | null;
  variant?: "bar" | "stepped";
}) {
  const percent = convictionToPercent(level);
  const color = convictionColor(level);

  if (variant === "stepped") {
    // Stepped bars (current thesis page design -- keep it)
    return (
      <div className="flex gap-0.5 items-end h-5">
        {CONVICTION_STEPS.map((step, i) => {
          const isActive = i <= CONVICTION_STEPS.indexOf(level ?? "New");
          const height = 6 + i * 2.5;
          return (
            <Tooltip key={step}>
              <TooltipTrigger asChild>
                <div
                  className="flex-1 rounded-[1px] transition-all"
                  style={{
                    height: `${height}px`,
                    background: isActive ? color : "rgba(255,255,255,0.04)",
                    opacity: isActive ? 0.8 : 0.3,
                  }}
                />
              </TooltipTrigger>
              <TooltipContent side="top">
                <p className="text-xs">{step}</p>
              </TooltipContent>
            </Tooltip>
          );
        })}
      </div>
    );
  }

  // Simple bar variant for list views
  return (
    <div className="flex items-center gap-2">
      <Progress
        value={percent}
        className="h-1.5 flex-1"
        style={{ "--progress-foreground": color } as React.CSSProperties}
      />
      <Badge variant="outline" style={{ color, borderColor: color }}>
        {level ?? "New"}
      </Badge>
    </div>
  );
}
```

### 5.3 Action Card with HoverCard Preview

```tsx
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card";

function ActionCardWithPreview({ action, thesisLookup }) {
  return (
    <Card className="group cursor-pointer transition-all hover:border-white/10">
      <CardHeader className="flex flex-row items-center gap-2 pb-2">
        <Badge variant={`priority-${action.priority.split(" ")[0].toLowerCase()}`}>
          {action.priority.split(" ")[0]}
        </Badge>
        <Badge variant="outline" className="text-t3">
          {action.action_type}
        </Badge>
        <Badge variant={`status-${action.status.toLowerCase()}`} className="ml-auto">
          {action.status}
        </Badge>
      </CardHeader>

      <CardContent>
        <h3 className="text-[15px] font-semibold leading-snug mb-1">
          {action.action}
        </h3>

        {action.thesis_connection && (
          <HoverCard>
            <HoverCardTrigger asChild>
              <Badge variant="thesis" className="cursor-pointer">
                {action.thesis_connection}
              </Badge>
            </HoverCardTrigger>
            <HoverCardContent className="w-80">
              {/* Rich thesis preview */}
              <div className="space-y-2">
                <h4 className="font-semibold">{action.thesis_connection}</h4>
                <ConvictionGauge level={thesisData?.conviction} variant="bar" />
                <p className="text-sm text-muted-foreground line-clamp-3">
                  {thesisData?.core_thesis}
                </p>
              </div>
            </HoverCardContent>
          </HoverCard>
        )}
      </CardContent>

      <CardFooter className="text-xs font-mono text-t3">
        {formatRelativeDate(action.created_at)}
        {action.relevance_score != null && (
          <span className="ml-auto">Score: {action.relevance_score.toFixed(1)}</span>
        )}
      </CardFooter>
    </Card>
  );
}
```

### 5.4 Keyboard Shortcut Help Dialog

```tsx
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Kbd, KbdGroup } from "@/components/ui/kbd";
import { Separator } from "@/components/ui/separator";

function KeyboardShortcutHelp({ open, onOpenChange }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4">
          <ShortcutSection title="Global">
            <ShortcutRow keys={["Cmd", "K"]} description="Command palette" />
            <ShortcutRow keys={["G", "A"]} description="Go to Actions" />
            <ShortcutRow keys={["G", "T"]} description="Go to Thesis" />
            <ShortcutRow keys={["?"]} description="This help" />
          </ShortcutSection>
          <Separator />
          <ShortcutSection title="Action Triage">
            <ShortcutRow keys={["J"]} description="Next action" />
            <ShortcutRow keys={["K"]} description="Previous action" />
            <ShortcutRow keys={["A"]} description="Accept" />
            <ShortcutRow keys={["D"]} description="Dismiss" />
            <ShortcutRow keys={["F"]} description="Defer" />
            <ShortcutRow keys={["Z"]} description="Undo" />
            <ShortcutRow keys={["X"]} description="Toggle selection" />
          </ShortcutSection>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function ShortcutRow({ keys, description }: { keys: string[]; description: string }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm text-t2">{description}</span>
      <KbdGroup>
        {keys.map((k) => <Kbd key={k}>{k}</Kbd>)}
      </KbdGroup>
    </div>
  );
}
```

### 5.5 Filter Bar with Combobox + ToggleGroup

```tsx
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

function ActionFilterBar() {
  return (
    <div className="flex items-center gap-3 flex-wrap">
      {/* Quick status toggle -- most-used filter */}
      <ToggleGroup type="single" value={currentStatus} onValueChange={handleStatusChange}>
        <ToggleGroupItem value="All">All</ToggleGroupItem>
        <ToggleGroupItem value="Proposed">
          Proposed <Badge variant="count" className="ml-1">{pendingCount}</Badge>
        </ToggleGroupItem>
        <ToggleGroupItem value="Accepted">Accepted</ToggleGroupItem>
        <ToggleGroupItem value="Dismissed">Dismissed</ToggleGroupItem>
      </ToggleGroup>

      <Separator orientation="vertical" className="h-6" />

      {/* Secondary filters as Select dropdowns */}
      <Select value={currentPriority} onValueChange={handlePriorityChange}>
        <SelectTrigger className="w-[150px]">
          <SelectValue placeholder="Priority" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="All">All Priorities</SelectItem>
          <SelectItem value="P0">P0 - Act Now</SelectItem>
          <SelectItem value="P1">P1 - This Week</SelectItem>
          <SelectItem value="P2">P2 - This Month</SelectItem>
          <SelectItem value="P3">P3 - Backlog</SelectItem>
        </SelectContent>
      </Select>

      {hasFilters && (
        <Button variant="ghost" size="sm" onClick={clearAll}>
          Clear filters
        </Button>
      )}
    </div>
  );
}
```

### 5.6 Loading States with Skeleton

```tsx
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

function ActionCardSkeleton() {
  return (
    <Card>
      <CardHeader className="flex flex-row gap-2 pb-2">
        <Skeleton className="h-5 w-8 rounded" />
        <Skeleton className="h-5 w-16 rounded" />
        <Skeleton className="h-5 w-14 rounded ml-auto" />
      </CardHeader>
      <CardContent className="space-y-2">
        <Skeleton className="h-5 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </CardContent>
    </Card>
  );
}

function ActionListSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <ActionCardSkeleton key={i} />
      ))}
    </div>
  );
}
```

---

## 6. Design Tokens & Typography

### 6.1 Existing Design Tokens (Preserve)

The current token system is strong. Keep it and map it to shadcn's CSS variable convention:

```css
/* Current tokens -- KEEP THESE */
--color-bg: #08080c;
--color-card: #0f0f16;
--color-elevated: #16161f;
--color-subtle-border: rgba(255, 255, 255, 0.06);
--color-flame: #ff5722;
--color-amber: #ffab00;
--color-cyan: #00e5ff;
--color-violet: #b388ff;
--color-green: #69f0ae;
--color-t1: #eeedf2;
--color-t2: #908e9b;
--color-t3: #56545f;

/* Map to shadcn convention (add these) */
--background: 240 33% 4%;         /* #08080c */
--foreground: 252 9% 94%;         /* #eeedf2 = t1 */
--card: 240 21% 7%;               /* #0f0f16 */
--card-foreground: 252 9% 94%;
--popover: 240 21% 7%;            /* same as card */
--popover-foreground: 252 9% 94%;
--primary: 14 100% 56%;           /* #ff5722 = flame */
--primary-foreground: 240 33% 4%;
--secondary: 240 15% 10%;         /* #16161f = elevated */
--secondary-foreground: 252 9% 94%;
--muted: 240 15% 10%;
--muted-foreground: 249 5% 35%;   /* #56545f = t3 */
--accent: 240 15% 10%;
--accent-foreground: 252 9% 94%;
--destructive: 14 100% 56%;       /* flame */
--border: 0 0% 100% / 0.06;      /* subtle-border */
--input: 0 0% 100% / 0.06;
--ring: 14 100% 56%;              /* flame for focus rings */
--radius: 0.75rem;
```

### 6.2 Typography (Preserve)

The current font stack is distinctive and strong -- no changes needed:

| Role | Font | Weight | Current |
|------|------|--------|---------|
| Sans (body) | DM Sans | 300-700 | Used for body text, UI |
| Serif (headlines) | Instrument Serif | Regular + Italic | Used for page titles |
| Mono (data) | JetBrains Mono | 400, 500, 700 | Used for labels, badges, data |

### 6.3 Spacing Scale

Keep the existing tight spacing that gives the editorial feel:

| Token | Value | Usage |
|-------|-------|-------|
| `gap-0.5` | 2px | Between badge elements, conviction bars |
| `gap-1.5` | 6px | Between pills/tags |
| `gap-2` | 8px | Between inline elements |
| `gap-3` | 12px | Between cards, list items |
| `p-3` | 12px | Compact card padding |
| `p-5` | 20px | Standard card padding |
| `mb-4` | 16px | Between section label and content |
| `mb-8` | 32px | Between page header and content |
| `mb-10` | 40px | Between major sections |
| `mb-12` | 48px | Between hero sections |

### 6.4 Custom Badge Variants

Define custom variants using `cva` for the AI CoS color system:

```tsx
// badge.tsx -- extend with custom variants
import { cva } from "class-variance-authority";

const badgeVariants = cva(
  "inline-flex items-center rounded px-2 py-0.5 text-[10px] font-mono font-bold transition-colors",
  {
    variants: {
      variant: {
        default: "bg-white/4 text-t3 border border-subtle-border",
        outline: "border border-subtle-border text-t3",
        // Priority variants
        "priority-p0": "bg-flame/12 text-flame",
        "priority-p1": "bg-amber/10 text-amber",
        "priority-p2": "bg-cyan/8 text-cyan",
        "priority-p3": "bg-violet/8 text-violet",
        // Status variants
        "status-proposed": "bg-amber/8 text-amber",
        "status-accepted": "bg-green/10 text-green",
        "status-dismissed": "bg-white/4 text-t3",
        "status-done": "bg-green/15 text-green",
        // Conviction variants
        "conviction-new": "bg-cyan/8 text-cyan",
        "conviction-evolving": "bg-cyan/8 text-cyan",
        "conviction-low": "bg-amber/10 text-amber",
        "conviction-medium": "bg-amber/10 text-amber",
        "conviction-high": "bg-green/10 text-green",
        // Functional
        thesis: "bg-violet/8 text-violet",
        count: "bg-white/6 text-t2 text-[9px] rounded-full min-w-[18px] text-center",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);
```

### 6.5 Sonner Theme Configuration

```tsx
// layout.tsx
import { Toaster } from "@/components/ui/sonner";

<Toaster
  theme="dark"
  position="bottom-right"
  toastOptions={{
    style: {
      background: "var(--color-card)",
      border: "1px solid var(--color-subtle-border)",
      color: "var(--color-t1)",
      fontFamily: "var(--font-mono)",
      fontSize: "12px",
    },
    actionButtonStyle: {
      background: "var(--color-flame)",
      color: "var(--color-bg)",
      fontWeight: 600,
    },
  }}
/>
```

---

## 7. Migration Strategy

### Phase 1: Foundation (no visual changes yet)

1. **Install shadcn CLI**: `npx shadcn@latest init` -- configure for dark theme, Tailwind v4, New York style
2. **Install Tier 1 components**: command, sonner, sidebar, sheet, drawer, kbd, skeleton
3. **Add `cn()` utility**: Tailwind-merge + clsx helper
4. **Map CSS variables**: Add shadcn variable mappings alongside existing tokens
5. **Add `<Toaster />` to layout**: Sonner ready globally

### Phase 2: App Shell Transformation

6. **Replace `<Nav />` with `<Sidebar />`**: Desktop sidebar + mobile bottom tabs
7. **Add Command Palette**: Global Cmd+K with navigation + search
8. **Add Kbd hints**: Show keyboard shortcut hints in tooltips and command items
9. **Add Skeleton states**: Loading placeholders for every data section

### Phase 3: Action Triage Upgrade

10. **Replace action cards with shadcn Card + Badge**: Standardised styling
11. **Replace filter bar with ToggleGroup + Select**: More polished filters
12. **Replace undo toast with Sonner**: Built-in undo action pattern
13. **Add Sheet detail panel**: Click card -> slide-in detail (desktop)
14. **Add Drawer detail panel**: Click card -> slide-up detail (mobile)
15. **Add keyboard shortcuts**: J/K navigation, A/D/F triage, Z undo
16. **Add HoverCard previews**: Thesis connection hover preview

### Phase 4: Thesis Dashboard Upgrade

17. **Replace thesis cards with Card + Progress gauge**
18. **Add Tabs to thesis detail**: Core | Evidence | Analysis | Intel
19. **Add Collapsible evidence**: Standardised expand/collapse
20. **Add HoverCard for thesis in other pages**

### Phase 5: Polish & Power Features

21. **Add Resizable split pane**: Desktop action triage list + detail
22. **Add ContextMenu**: Right-click on cards
23. **Add Breadcrumb**: Navigation path in detail views
24. **Add Carousel**: Mobile swipe-through triage mode
25. **Add Empty states**: Standardised zero-state with icons + messages

### Dependencies to Install

```bash
# shadcn components (each installs its Radix/Vaul dependency automatically)
npx shadcn@latest add command sonner sidebar sheet drawer kbd skeleton
npx shadcn@latest add card badge tabs toggle-group select separator
npx shadcn@latest add progress collapsible hover-card tooltip dialog
npx shadcn@latest add resizable dropdown-menu button-group scroll-area
npx shadcn@latest add breadcrumb carousel context-menu checkbox avatar
npx shadcn@latest add table empty spinner input alert

# Additional peer dependencies
npm install cmdk sonner vaul react-resizable-panels lucide-react
npm install class-variance-authority clsx tailwind-merge
```

---

## Appendix: Reference Apps & What to Steal

| App | Pattern to Steal | Our Equivalent |
|-----|-----------------|----------------|
| **Linear** | Command palette as primary navigation; keyboard-first everything; sidebar with collapsible groups; contextual right panels | Cmd+K palette, J/K navigation, sidebar, Sheet detail |
| **Superhuman** | Single-key triage (E=done, H=snooze); undo bar; auto-advance after action; stripped-down UI focused on decision speed | A=accept, D=dismiss, F=defer; Sonner undo; auto-advance to next card |
| **Arc Browser** | Split view; pinned sidebar; spaces for context switching | Resizable split pane; sidebar with collapsible nav |
| **Notion** | Hover previews for linked entities; slash command for everything; breadcrumb navigation | HoverCard for thesis/companies; Command palette; Breadcrumb |
| **Raycast** | Command palette categories with fuzzy search; keyboard shortcut discovery | Command groups: Navigation, Actions, Thesis, Commands |
| **Figma** | Right-side inspector panel that updates with selection | Sheet/Resizable panel showing selected item detail |

---

## Sources

- [shadcn/ui Components](https://ui.shadcn.com/docs/components)
- [shadcn/ui October 2025 New Components](https://ui.shadcn.com/docs/changelog/2025-10-new-components)
- [shadcn/ui March 2026 CLI v4](https://ui.shadcn.com/docs/changelog/2026-03-cli-v4)
- [How Linear Redesigned Its UI](https://linear.app/now/how-we-redesigned-the-linear-ui)
- [Superhuman Keyboard Shortcuts](https://help.superhuman.com/hc/en-us/articles/45191759067411-Speed-Up-With-Shortcuts)
- [Command Palette Patterns](https://www.commandpalette.org/)
- [shadcn Dashboard Examples](https://ui.shadcn.com/examples/dashboard)
- [Responsive Dialog+Drawer Pattern](https://www.nextjsshop.com/resources/blog/responsive-dialog-drawer-shadcn-ui)
