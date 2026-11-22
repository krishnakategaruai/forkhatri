# Mangalya wireframes, part B (as built, read from code 2026-11-22)

Source: `mangaly-web/app/*`, `components/*`, `locales/en/*.json`. Static code reading only; no screen was opened. Pixel sizes are not verified. SCR ids follow the addendum in `03-ux.md` (line 2455). All API paths are relative to the Mangalya API base. Role words: **candidate** = member with own profile; **family** = parent, sibling, relative or guardian acting in a candidate's Home Circle; **broker** = marriage agent or relationship manager (RM).

Shared shell (every signed-in screen unless noted): bottom bar with five tabs `Home | Discover | Circle | Messages | Me` (Circle shows `counts.pending_requests`, Messages shows `counts.unread_messages`); a Menu drawer adds `Wedding arrangements`, `Guides`, `Marriage agents` (or `Workspace` for agents) and `How Mangalya works`. Thread/detail routes (`/messages/[id]`, `/wedding/[id]`, `/guides/[slug]`) are treated as detail screens. Legacy sign-in routes have no shell.

---

## Screen part: Messages

### SCR-13 Messages inbox (/messages)

Layout file `app/messages/layout.tsx` renders `ConversationList` on every `/messages*` route. On a phone only one pane shows: the inbox at `/messages`, the thread when one is open.

```
+--------------------------------------+
| Messages                [1] [2] [3]  |  header
+--------------------------------------+
| (face) [lock]  Varun        Today    |<-[4] incognito row
|        Incognito  You: see you soon  |
|--------------------------------------|
| (face)(face)  Varun's family & yours |<-[5] family row
|        Families  Lata: hello      (2)|<-[6] unread badge
|--------------------------------------|
| (face)  Lakshmi              Yesterday|<-[7] direct row
|        Thank you!                    |
|                                      |
+--------------------------------------+
| Home  Discover  Circle  Messages  Me |
+--------------------------------------+
[1] pencil (compose)  [2] hub link? no: account button is [3]
```

Correction of the header callouts: [1] is the compose pencil, [2] is the account button; there is no hub link here.

| # | Element | What it does | Data (API field) | States | Next |
|---|---|---|---|---|---|
| 1 | Compose pencil, label `New message` | Toggles the people picker in place; shows a close icon while open | none | Hidden while the list is empty or loading (the empty state has its own button) | Picker (below) |
| 2 | Account button | Account menu (language, roles, sign out) | session | all roles | menu |
| 4 | Incognito row: lock badge, name, `Incognito` tag | Opens the candidates' private session | `GET /conversations` rows: `kind=candidate`, `connection_id`, `other_name`, `other_photo_url`, `last_message_at`, `last_message`, `unread_count` | Candidate only (two connected candidates) | `/messages/[connectionId]` |
| 5 | Families' group row: faces, `Families` tag | Opens the optional group of both families. Named `{{name}}'s family & yours` when you are a candidate, else `{{a}} & {{b}}` | `participants[]` (role=candidate), `joined` | Family and candidate | `/messages/[id]?kind=family` |
| 6 | Unread badge | Count of unread | `unread_count` | Row bold when above 0 | |
| 7 | Direct row, no tag | One-to-one chat, kept | `conversation_id`, `other_name`; preview prefixed `You: ` when mine, `Name: ` for others in a family chat | all roles | `/messages/[conversation_id]?kind=direct` |
| - | Preview text | Last message; a system line shows its translated key | `last_message.content`, `kind` | Empty: `No messages yet` | |

Whole-screen states: loading shows three skeleton rows; refresh every 8 s while visible. Empty (no rows): icon, `No messages yet`, `Write to someone in your family, or to the family of a match you are connected with.`, button `New message`. Error: list returns empty (no explicit error text). Desktop pane placeholder (`/messages` at wide width): `Your messages` / `Choose a conversation, or start a new one.`

#### New message picker (replaces the list in place)

```
+--------------------------------------+
| Messages                      [ X ]  |
+--------------------------------------+
| ( search )  Search people            |<-[1]
|--------------------------------------|
| Your family                          |<-[2] group title
|  (face) Lakshmi Reddy                |
|         mother of Ananya             |<-[3]
| Varun's family                       |
|  (face) Suresh   father of Varun     |
|                                      |
| You can message your own family, and |
| the family of anyone you are         |
| connected with. Two connected        |
| candidates talk in their private     |
| session instead.                     |
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Search people | Filters by `display_name` | query string, client side | | |
| 2 | Group heading: `Your family` or `{{name}}'s family` | Groups contacts by side | `mine`, `side_account_id`, `side_name` | Loading: `Loading…` | |
| 3 | Person button: name and link line (`{{relation}} of {{name}}` or `Looking for a match`) | Opens or creates a direct chat | `GET /messages/direct/contacts` -> `account_id`, `display_name`, `photo_url`, `role`, `relation`; then open direct | No contacts: `No one to message yet. People appear here once they are in your Home Circle, or in the family of someone you are connected with.` plus button `Invite family to your circle` | `/circle` or `/messages/[id]?kind=direct` |

### SCR-13 Message thread (/messages/[connectionId]?kind=candidate|direct|family)

One screen, three kinds. Candidate kind (no query) is the incognito session; its page is darker ("night mood") with a lock on the avatar. Polls every 3 s while visible.

```
+--------------------------------------+
| <   (face)[lock]  Varun        ( ... )|  header
|        Incognito · nothing is kept   |
+--------------------------------------+
|            (big face)                |<-[3]
|              Varun                   |
| A private session. Leave it, or stay |
| quiet for 30 minutes, and everything |
| here is deleted for both of you. A   |
| browser cannot stop screenshots, so  |
| write what you would say in person.  |
|                                      |
|            Today                     |
| (their bubble)                       |
|              (my bubble)  10:41      |
|  -- You are connected. ... --        |<-[5] system line
| [Namaste! 🙏] [Hi Varun, your ...]   |<-[6] starters
+--------------------------------------+
| ( Message in incognito…      ) (>)   |<-[7]
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Back arrow, `Back` | Returns to inbox (incognito session is ended on leave) | | | `/messages` |
| 2 | Header name and subtitle | Name of other person or `{{a}} & {{b}}`; subtitle `Incognito · nothing is kept`, or the link (`father of Divya`), or `Looking for a match`, or `{{count}} people · both families` | `GET /messages/{id}/people` -> `display_name`, `role`, `relation`, `side_name`, `is_me` | Direct with a candidate: avatar links to profile | `/profile/[accountId]` |
| 3 | Intro block | One note per kind: incognito `sessionNote`; direct `Your conversation, kept like any chat. Only the two of you can read it.`; family `The families’ conversation. Everyone in both Home Circles can read it, and it is kept for as long as the two of you are connected.` | | | |
| 4 | Day separators `Today`, `Yesterday`, date | Group by day | `sent_at` | | |
| 5 | System line | Platform line in reader's language: `You are connected. Only the two of you can read this conversation.` or `The families’ chat is open. Everyone in both Home Circles can read it.` | `kind=system`, `content` is a key | | |
| 6 | Starter chips (`Namaste! 🙏`, `Hi {{name}}, your profile made me smile`, `What does a perfect Sunday look like for you?`) | Fill the composer, not sent | | Shown only until anyone has written, and not in family kind | |
| 7 | Composer and send arrow, `Send`; placeholder `Type a message…` (incognito: `Message in incognito…`) | `POST /messages/{id}` (kind query for direct/family) | `content` | Sending: input disabled; errors line above: `We couldn't reach Mangalya. Check your connection and try again.` or `You're sending messages too quickly. Please slow down.` | refreshes list |
| 8 | Family kind bubbles | Other side's messages show face and writer label `Name · relation of Name`, coloured by side (a or b) | `sender_name`, `sender_relation`, `sender_side_account_id` | | |
| - | Loading | Sacred loader (held at least one second) | | | |
| - | Gone | `You can only message a connection you've both accepted.` and link `Messages` (roster empty) | | | `/messages` |

Roles: candidate sees all three kinds; family sees direct and the families' group (cannot open incognito). Incognito ends (all messages deleted for both) on leaving the page, hiding the tab, `End chat`, or 30 minutes of silence.

#### Thread menu (... button, `More`)

```
+--------------------------------------+
| <   Varun                    ( ... )  |
|                  +-----------------+ |
|                  | Family chat     | |<-[1] incognito only
|                  | Open a chat with| |
|                  | both families   | |
|                  | View profile    | |<-[2]
|                  | Report          | |<-[3]
|                  | Block           | |<-[4] red
|                  | End chat        | |<-[5] red, incognito only
|                  | Deletes ... both| |
|                  +-----------------+ |
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | `Family chat` / `Open a chat with both families` | Creates/opens the families' group | `POST /conversations/{id}/family/open` | Incognito kind only | `?kind=family` |
| 2 | `View profile` | | `other.account_id` | Not in family kind; only when the other is a candidate | `/profile/[id]` |
| 3 | `Report` | Opens report panel | | all kinds | panel below |
| 4 | `Block` | Opens block panel | | Not in family kind; needs the other's profile id | panel below |
| 5 | `End chat` / `Deletes everything here for both of you` | Closes and deletes the session | `closeConversation` | Incognito only | `/messages` |

#### Report and block panels (inline panels at the top of the thread)

```
+--------------------------------------+
| Who are you reporting?               |<-[1] family kind only
| [Lakshmi · mother of Ananya] [..]    |
| Report Varun                         |
| [Harassment] [Fake profile]          |<-[2] reason chips
| [Inappropriate messages] [Asking for |
|  money] [Already married] [Under age]|
|  [Something else]                    |
| +----------------------------------+ |
| | Anything we should know          | |<-[3]
| | (optional)                       | |
| +----------------------------------+ |
| This chat, as it is right now, goes  |
| to Mangalya’s safety team with your  |
| report. Varun is not told who        |
| reported.                            |
|        [ Cancel ] [ Send report ]    |<-[4]
+--------------------------------------+
| Block Varun? They will not see you or|
| message you again, and this chat     |
| closes.        [ Cancel ] [ Block ]  |
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | `Who are you reporting?` chips | Pick the writer | `people[]` except me | Family kind only | |
| 2 | Reason chips (`reason.*`) | Pick one | REPORT_REASONS | `Send report` disabled until person and reason chosen | |
| 3 | Details textarea | Optional | `details` | | |
| 4 | `Send report` | `POST /messages/{id}/report` with thread snapshot | `reason`, `details`, reported account | Success: notice `Thank you. Our safety team will look at this.`; failure: error text above composer | stays |
| - | `Block` confirm | Blocks the profile, ends an incognito session | `block(otherProfileId)` | | `/messages` |

#### SCR-13 at 1280px (two panes)

```
+---------------------------+--------------------------------------------+
| Messages        [pen][acc]| < (face) Varun · Incognito · nothing kept ...|
|---------------------------|--------------------------------------------|
| (f) Varun        Today    |            (big face) Varun                 |
|     Incognito You: ...    |            intro note                       |
| (f)(f) Varun's family (2) |            Today                            |
| (f) Lakshmi   Yesterday   |   (their bubble)        (my bubble) 10:41   |
|                           |                                            |
| [open row has aria-current]| ( Message in incognito…            ) (>)   |
+---------------------------+--------------------------------------------+
  left: ConversationList      right: thread, or `Your messages` placeholder
```

Both panes show at once (`mpane__list` and `mpane__main`); the list marks the open row by id and `kind` (an incognito session and a families' chat share a connection id). Back arrow is still present in the thread (unverified whether it is hidden by CSS at desktop width).

---

## Screen part: Home Circle

### SCR-12 Home Circle (/circle)

Header: title `Home Circle`, hub link (`ForKhatriHubLink`), account button; under it the context chip. The screen renders three variants.

**A. Candidate (own context)**

```
+--------------------------------------+
| Home Circle              [hub] [acc] |
| ( ● Finding a bride for you  Change )|<-[1] context chip
+--------------------------------------+
| The family members helping with this |
| search, and what each can see.       |<-[2]
| ( Looking for — not answered yet )   |<-[3] only if unanswered
|                                      |
| +- Invitations for you --------------+|<-[4]
| | (f) Meena invites you into their  ||
| |   Home Circle as their sister     ||
| | [ Accept ]  Decline               ||
| +------------------------------------+|
| +- Contact requests ----------------+|<-[5]
| | Lakshmi wants to share your phone ||
| | number with a match               ||
| | Only your phone number is shared..||
| | [ Approve ]  Decline              ||
| +- Notes from family ---------------+|<-[6]
| | (anon) 29 yrs · Pune              ||
| | Aunt wants you to read a note ...  ||
| | [ Read note ]  Not now            ||
| +- Members -------------------------+|<-[7]
| | Home  (2)                         ||
| | (f) Lakshmi Reddy  [You?]  Remove ||
| |     Mother · Joined 3 Oct 2026    ||
| |     Mother or father? [chips]     ||<-[8] old rows only
| | Relatives (1) ...                 ||
| +- Add family to your circle -------+|<-[9]
| | Their phone number or email ...   ||
| | [ Send invitation ]               ||
| | Joining someone else's circle     ||
| | instead?                          ||<-[10]
| +- Requests you sent ---------------+|<-[11]
| +- Suggestions from your circle ----+|<-[12]
+--------------------------------------+
| Home  Discover  Circle  Messages  Me |
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Context chip: `Finding a {{what}} for you` / `{{name}}'s search`, `Change` | Opens context switcher (sheet below) when there is more than one context | `GET /home-circle/contexts` -> `own_profile.looking_for`, circles | Single context: no `Change` | switcher |
| 2 | Blurb | Static text | | | |
| 3 | Chip `Looking for — not answered yet` | Shown only if `looking_for` is null | `own_profile.looking_for` | Answered: hidden (context line says it) | |
| 4 | `Invitations for you` card; rows `{{name}} invites you into their Home Circle as their {{relationship}}` or `...asks to join your Home Circle as your ...` | `Accept` reloads the page to refresh contexts; `Decline` removes row | `GET /home-circle/invitations/pending` -> `id`, `inviter_name`, `relationship_type`; `POST .../accept`, `.../decline` | Hidden when none | reload |
| 5 | `Contact requests` card | `Approve` / `Decline` sharing own phone number with one match | `GET /home-circle/contact-requests` -> `id`, `candidate_name`; approve/decline POSTs | Hidden when none | |
| 6 | `Notes from family`: a request row (`Read note` / `Not now`) or a shared note (`From {{name}} · {{date}}`) | Words visible only after `Read note`; `Not now` shares nothing | `GET /home-circle/notes/requests`, `/notes/shared`; `notes/{id}/read`, `/decline`; match snippet via `getSnippet` (age, locality, education, profession; photo hidden) | Hidden when none. Match row links to profile | `/profile/[id]` |
| 7 | `Members` card, groups `Home` and `Relatives` with counts | Lists members; candidate can `Remove` | `GET /home-circle/members` -> `membership_id`, `member_name`, `member_account_id`, `relationship_type`, `relation`, `joined_at`; `DELETE /home-circle/members/{id}` | Empty: family illustration and `No one has joined this Home Circle yet. Invite a family member to join.` The whole card is hidden when empty and the candidate has no own profile | |
| 8 | Relation chips under a row with no exact relation | One tap states `Mother or father?` / `Brother or sister?` / `Which relative?` | `PATCH /home-circle/members/{id}/relation` | Shown to the candidate or to the member themself | |
| 9 | `Add family to your circle` invite form (CircleInvite, own mode) | Field `Name or phone number`, chips of relation, button `Send invitation` (`Sending…`) | `GET /home-circle/people?q=`, `POST /home-circle/invite` | Result: `Invitation sent to {{name}}.`; no match: `No one on ForKhatri matches that. You can type their phone number instead.` or `Not on ForKhatri yet — we will invite {{number}} by phone.`; errors `You can't invite yourself.`, `There's already a pending invitation for that phone number or email.`, `We couldn't reach Mangalya. Check your connection and try again.` | |
| 10 | Quiet link `Joining someone else's circle instead?` / `Adding family to your own circle instead?` | Switches the form between own and join (`Join your family's Home Circle`, button `Ask to join`) | | Members with no own profile (typically a parent) see only the join form, and only when no invitation is pending | |
| 11 | `Requests you sent` | Each row: match snippet, status `Waiting for a reply / Accepted / Declined / Withdrawn`, `sent by you / sent by family / sent by {{name}}` and date | `GET /connections/sent` | Shown only when there are rows (own context) | `/profile/[id]` |
| 12 | `Suggestions from your circle` | Row: first name and age, education, profession, locality; `Suggested by your {{relationship}}`; optional quoted note; `Suggestion — no action has been taken on your behalf.` | `GET /home-circle/suggestions` -> `suggested_profile_id`, `suggested_by_relationship_type`, `suggested_by_is_you`, `note` | Hidden when none | |

Loading: sacred loader, at least one second. Error: lists fall back to empty (no error banner). Desktop: members and the invite form sit side by side (`circle-grid`).

**B. Family (parent, sibling, relative, guardian) context**

```
+--------------------------------------+
| Home Circle              [hub] [acc] |
| ( ● Kavya Rao's search       Change )|<-[1]
+--------------------------------------+
| +- (face) Kavya Rao -----------------+|<-[2]
| | In Kavya's Home Circle as Father   ||
| | (Looking for ...)  (3 people helping)|
| | You can look for matches and send  ||
| | requests for Kavya. A request goes ||
| | out as Kavya's, with your name on  ||
| | it so everyone knows who sent it.  ||
| | [ Find matches for Kavya ]         ||<-[3]
| +- Invitations for you / Contact req.+|
| +- Members (no Remove) --------------+|<-[4]
| +- Add someone to Kavya's circle ----+|<-[5]
| +- Requests sent for Kavya -----------+|<-[6]
| +- Suggested to Kavya ---------------+|<-[7]
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Context chip | Switch between own search and each candidate you help | `contexts.circles[]` | | |
| 2 | Candidate card | Name and role: `In {{name}}'s Home Circle as {{relationship}}`; chips: looking-for (only if unset) and `{{count}} person helping / people helping` | `family.candidate_name`, `relation`, `relationship_type`, `looking_for` | | |
| 3 | `Find matches for {{name}}` | Go to Discover in that context | | | `/discover` |
| 4 | Members | Same list; your own row has `You`; no remove (removal is the candidate's decision) | `GET /home-circle/members?for_candidate=` | Empty: `You're the only one in {{name}}'s Home Circle so far.` | |
| 5 | `Add someone to {{name}}'s circle` (`A sibling, an aunt, a family friend who knows the families. They join once they accept.`) | Invite another relative | `POST /home-circle/invite` with candidate id | | |
| 6 | `Requests sent for {{name}}` | | `/connections/sent` filtered by `subject_account_id` | Empty: `No requests have gone out for {{name}} yet.` | |
| 7 | `Suggested to {{name}}` | Rows worded `You suggested this to {{name}}` or `Suggested by {{name}}'s {{relationship}}`, `Only a suggestion. No request has been sent for {{name}}.` | | Hidden when none | |

**C. Context switcher sheet (from the chip)**

```
+--------------------------------------+
|              ───                     |
| Whose search are you viewing?   [x]  |
|--------------------------------------|
| ( ) You              Your own profile|<-[1]
| ( ) Kavya Rao                        |<-[2]
|     You're in this circle as: Father |
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | You row | Switch to own search; announces `Now viewing your own search` | `own_profile` | Absent when the member has no own profile | `/circle` re-reads |
| 2 | Candidate row(s) | Switch to `{{name}}'s search`; announces `Now viewing {{name}}'s search`; choice stored in `mangaly.activeContext` (local storage) | `circles[]` | | |

---

## Screen part: Wedding arrangements and Guides

### SCR-16 Wedding arrangements list (/wedding)

Menu drawer destination (not in the bottom bar). Family members see the list for the candidate whose context is active.

```
+--------------------------------------+
| Wedding arrangements           [acc] |
| ( ● Kavya Rao's search       Change )|<-[1]
+--------------------------------------+
| After a family accepts, plan the     |
| next steps together: where to meet   |
| first, then halls, photography, cars |
| and more, near both families.        |<-[2]
|                                      |
| +----------------------------------+ |
| | (face)  With Varun             > | |<-[3]
| |         First meeting            | |<-[4]
| +----------------------------------+ |
| | (face)  With Rahul             > | |
| |         Families agreed          | |
| +----------------------------------+ |
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Context chip | Switch whose matches are listed | contexts | Family role: the candidate's matches | |
| 2 | Intro | Static | | Shown only with rows | |
| 3 | Match row, `With {{name}}` | Opens the plan for that match | `GET /conversations` (non-direct, one per `connection_id`): `other_name`, `other_photo_url`, then `GET /wedding/stages?ids=` | Only matches the stage service confirms (accepted) | `/wedding/[connectionId]` |
| 4 | Stage line | Current stage name | `stage`: `first_meeting`, `families_agreed`, `wedding_fixed` | | |
| - | Loading | Sacred loader | | | |
| - | Empty | Icon, `This opens after a match`, `When a family accepts your request, or you accept theirs, you can plan the first meeting and the wedding here, together with them.`, button `Go to Discover` | | | `/discover` |

### SCR-16 Wedding plan for one match (/wedding/[connectionId])

```
+--------------------------------------+
| <        With Varun                  |
+--------------------------------------+
| Where things stand                   |<-[1]
| (1) First meeting - (2) Families     |<-[2] three steps
|     agreed - (3) Wedding date fixed  |
| Pelli choopulu: the families meet for|
| the first time. Choose a calm place  |
| near both of you.                    |<-[3]
| Both families see the same stage.    |
| Either family can change it.         |
| [Read: the first meeting between     |
|  families]                           |<-[4]
|                                      |
| [Cafés][Family restaurants] ...      |<-[5] category tabs
|                                      |
| (Near both families · Hyderabad)     |<-[6] shown if >1 centre
| (Near you) (Near them)               |
|                                      |
| Mangalya partner offers              |<-[7]
| +----------------------------------+ |
| | [photo] [Partner offer]   [share]| |
| | Meena Garden Hall                | |
| | 10% off · ...                    | |
| | 1.1 km · Checked by Mangalya     | |
| | [Map] [Call] [Website]           | |
| +----------------------------------+ |
| Places near Hyderabad                |<-[8]
| +----------------------------------+ |
| | [photo]  Representative photo [sh]| |<-[9]
| | Name                             | |
| | 1.4 km · Vegetarian · address    | |
| | [Map] [Call] [Website]           | |<-[10]
| +----------------------------------+ |
| How this list is ordered: ...        |
| Places © OpenStreetMap contributors  |
| · List updated 12 Nov 2026           |
| > Photo credits                      |
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Header, back arrow `Back`, title `With {{name}}` | History back | `other_name` | Title falls back to `Wedding arrangements` | previous |
| 2 | Stage stepper (three buttons, current one pressed, earlier ones marked done) | Sets the shared stage; also resets the category tab to the stage's first category | `POST /wedding/{id}/stage` body `stage`; response `stage`, `categories[]` | Disabled while saving. Candidate and family can both change it | |
| 3 | Stage hint and `Both families see the same stage. Either family can change it.` | Hint per stage: `first_meeting`, `families_agreed` (`Both sides said yes. Book the hall early: good dates go three to six months ahead.`), `wedding_fixed` | | | |
| 4 | Guide link `Read: the first meeting between families` | | | Only at stage `first_meeting` | `/guides/the-first-meeting` |
| 5 | Category tabs (`Cafés`, `Family restaurants`, `Function halls`, `Jewellers`, `Sarees and wedding wear`, `Photographers`, `Caterers and cooks`, `Flowers and decoration`, `Bridal make-up and mehendi`, `Cars for the wedding`) | Loads places for that kind; which tabs show depends on stage | `StageInfo.categories` | | |
| 6 | Near selector `Near both families` / `Near you` / `Near them` with city label | Re-centres the search | `GET /wedding/{id}/places?category&near` -> `centres[]`, `centre` | Shown only when there is more than one centre | |
| 7 | Partner offer cards (badge `Partner offer`, `{{n}}% off`, `Until {{date}}`, `Checked by Mangalya`) | Offers kept separate and always marked | `partners[]`: `name`, `photo`, `offer`, `discount_percent`, `verified`, `valid_until`, `terms`, `distance_km`, `latitude`, `longitude`, `phone`, `website` | If none: caption `Mangalya is arranging special prices with trusted places in {{city}}. They will appear here, clearly marked as partner offers.` | |
| 8 | `Places near {{city}}` list | Nearest first | `places[]`: `ref`, `name`, `photo`, `photo_source`, `distance_km`, `vegetarian`, `address`, `phone`, `website`, `latitude`, `longitude` | Empty: `We don't have places of this kind near {{city}} yet.` | |
| 9 | Photo label `Representative photo` (no own photo) or `Photo: Wikimedia Commons` link | Honest labelling of stock art | | | |
| 10 | `Map` / `Call` / `Website` links | Open maps app, dial, open site (https only) | `latitude`, `longitude`, `phone`, `website` | Call and Website only when present | external |
| 11 | Share icon on card, label `Share {{name}}` | Opens share sheet | | | Share sheet |

Whole-screen states: loading (sacred loader); `This match is not available any more.` when the stage service does not return the connection; `We couldn't load this. Please try again.` on place error; `Add your town to your profile to see places near you.` when no centre exists.

#### Share a place sheet

```
+--------------------------------------+
|              ───                     |
| Share this place                [x]  |
|--------------------------------------|
| Your family                          |
|  (face) Lakshmi (mother)    [Send]   |<-[1]
|  No one from your family is on       |
|  Mangalya yet. Add them in Circle.   |
| Together                             |
|  (faces) Both families' chat [Send]  |<-[2]
|          Everyone from both Home     |
|          Circles                     |
|  (face) Varun  Your private chat     |
|                           [Send]     |<-[3]
| [Share with another app]             |<-[4]
+--------------------------------------+
 after send: Sent to Lakshmi. [Open the chat] [Send to someone else]
 on failure: We couldn't send it. Please try again.
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Family row `Send` | Sends the place as a direct chat message (3 lines: pin, detail, map link) | `openDirect`, then `POST /messages/{id}?kind=direct` | Candidate's own side labelled `the one getting married`. Empty family: see wireframe | chat |
| 2 | `Both families' chat` | Sends into the families' group | kind family | | |
| 3 | `{{name}}` private chat | Sends into the incognito session | kind candidate | | |
| 4 | `Share with another app` | Device share | | | |

The chat draws such a message as a place card with `Open map` and `Shared place`.

### SCR-17 Guides list (/guides)

```
+--------------------------------------+
| Guides                         [acc] |
+--------------------------------------+
| Short guides for families: a better  |
| profile, good photos, staying safe,  |
| and the situations many families     |
| meet.                                |<-[1]
| Getting started                      |<-[2]
| +----------------------------------+ |
| | Title                          > | |<-[3]
| | one-line summary                 | |
| | (play) Video · 4 min read        | |
| +----------------------------------+ |
| A better profile ...                 |
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Intro | Static | | | |
| 2 | Category headings in order: `Getting started`, `A better profile`, `Photos and style`, `Safety`, `Family situations`, `After a match` | Group | `category` | Empty groups hidden | |
| 3 | Guide card | Opens the guide | `GET /guides` -> `slug`, `title`, `summary`, `minutes`, `has_video`, `category` (language follows app language) | Loading: loader. Error: `We couldn't load the guides. Please try again.` | `/guides/[slug]` |

Roles: same for all signed-in members.

### SCR-17 Guide (/guides/[slug])

```
+--------------------------------------+
| <        Safety                      |<-[1] category as title
+--------------------------------------+
| Guide title                          |
| summary                              |
| 4 min read                           |
| This guide is not in your language   |
| yet, so it is shown in English.      |<-[2]
| [ video player ]                     |<-[3]
| Heading                              |
| paragraph                            |
|  - point                             |<-[4]
| [ Open Circle ]                      |<-[5]
| More guides                          |<-[6]
+--------------------------------------+
```

| # | Element | What it does | Data | States | Next |
|---|---|---|---|---|---|
| 1 | Back | History back | | | previous |
| 2 | Language note | | `guide.language` vs app language | Only for a non-English app language | |
| 3 | Video | YouTube (privacy-enhanced embed) or any https video | `video_url` | Absent when none | |
| 4 | Sections | `h`, `p`, `points[]` | `sections[]` | | |
| 5 | Action button: `How Mangalya works`, `Open Circle`, `Edit my profile`, `Wedding arrangements`, else `Open in Mangalya` | Deep link inside the app | `action_href` (must start with `/`) | Absent when none | target |
| 6 | `More guides` | | | | `/guides` |

States: loader; `This guide is not available.` when missing.

---
