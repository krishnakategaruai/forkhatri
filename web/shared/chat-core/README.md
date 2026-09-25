# @forkhatri/chat-core

Shared conversation layout logic for ForKhatri module chats.

It answers one question — *how should this list of messages be shaped?* — and
nothing else. No React, no CSS, no i18n, no network. Modules keep their own
chat screens, styling, vocabulary and rules; they just stop re-deriving the
grouping arithmetic.

## What it provides

- `shapeConversation(messages, read, options)` — marks each message with
  `joinsAbove` / `joinsBelow` (merge into one shaped group), `startsBlock`
  (earns a visible timestamp) and `daySeparator`.
- `dayKey`, `clockTime`, and the tuned constants `GROUP_GAP_MS`,
  `BLOCK_BREAK_MS` and `CHAT_TIME_ZONE`.

Day separators come back as tokens (`today`, `yesterday`, `date`), never as
English text, because every ForKhatri surface ships in English, Hindi and
Telugu and the module owns its translations.

## Usage

Map your own message type through `read`, so you do not have to rename any
fields:

    import { shapeConversation } from '@forkhatri/chat-core';

    const rows = shapeConversation(messages, (m) => ({
      id: m.id,
      senderId: m.sender_account_id,
      sentAt: m.sent_at,
      kind: m.kind,
    }));

Each row carries the original message plus the shaping flags, so rendering
stays entirely the module's business.

## Adopting it in a module

The package is plain TypeScript source, consumed by a Next.js app with a
tsconfig path alias plus `transpilePackages`. See
`modules/MOD03-mangaly/mangaly-web` for a worked example.

## Origin

The grouping rules were worked out in MOD02 Milavn's chat v3 and reviewed by
the product owner. They were extracted here when MOD03 Mangaly needed the same
behaviour for a conversation with very different rules — an ephemeral session
that deletes for both people when either one leaves. Anything specific to one
module (Milavn's presence and mood avatars, Mangaly's session semantics and
candidate/family thread kinds) deliberately stays in that module.

MOD02 Milavn still has its own inline copy of this arithmetic. Pointing it at
this package is a separate, owner-approved change, because it edits another
module's files.
