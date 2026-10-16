# Frontend Architecture

## Framework

**React** was chosen over Vue and Svelte. Vue was considered — it has a gentler 
learning curve — but our hiring pool is much larger for React engineers. Svelte 
was rejected as too immature for a production app we'll maintain for years.

## State Management

**Zustand** over Redux and MobX. Redux requires too much boilerplate for our app 
size. MobX's magic (proxy-based reactivity) makes debugging harder. Zustand is 
minimal, TypeScript-friendly, and doesn't require a Provider wrapper.

## Styling

**Tailwind CSS** was chosen over CSS Modules and styled-components. CSS Modules 
work well but don't scale as well for a design system. styled-components adds 
runtime overhead and makes SSR more complex. Tailwind's utility-first approach 
gives consistent spacing/colors without a custom design system.

## Build Tool

**Vite** replaced Create React App. CRA is effectively unmaintained. Vite is 
significantly faster for dev server startup and HMR. esbuild for prod builds.

## Testing

**Vitest + React Testing Library** over Jest. Vitest is faster and shares Vite's 
config, eliminating the need for a separate babel/jest config. Testing Library 
encourages testing behaviour over implementation, which reduces brittle tests.

## Component Library

No third-party component library — we build our own small set of primitives. 
MUI (Material UI) was rejected because it imposes Google's design language. 
Radix UI was considered for headless components and may be adopted incrementally 
for complex components (comboboxes, dialogs).
