# Milavn API reference (as built, 2026-11-22)

Generated from the running service `GET http://localhost:8001/openapi.json` (205 operations; plus 1 added 2026-11-22, see end of file) and the route files in `milavn-service/app/api/routes/`. Auth column is read from each handler's dependency (`CurrentMember`, `OptionalMember`, `Moderator`). Request bodies are named by their Pydantic schema; `*` marks required query parameters. Error codes beyond those listed: 401 not signed in, 403 not allowed (RLS or business rule), 409 conflict, 422 validation, 429 rate limited, 503 identity service unavailable (fail closed). Internal route `GET /internal/v1/insights/members` (platform service key, hidden from OpenAPI) is listed at the end. All IDs here are `API-nnn` for traceability.

Common headers: `X-Milavn-Language` (en/hi/te/mr/kn), `Idempotency-Key` (mutations that accept it), session cookie `fk_session` (set by the ForKhatri entrance, not by Milavn). Writes from a browser must come from an allowed Origin (CORS list).

## Contents

- [admin](#admin) (5)
- [calendar](#calendar) (5)
- [chat](#chat) (12)
- [circle-social](#circle-social) (14)
- [circles](#circles) (50)
- [conversation](#conversation) (17)
- [discovery](#discovery) (8)
- [events](#events) (12)
- [feedback](#feedback) (3)
- [identity](#identity) (2)
- [notifications](#notifications) (7)
- [occurrences](#occurrences) (22)
- [ops](#ops) (1)
- [payments](#payments) (8)
- [people](#people) (11)
- [privacy](#privacy) (2)
- [profile](#profile) (9)
- [public](#public) (2)
- [safety](#safety) (5)
- [tickets](#tickets) (10)


## admin

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-001 | GET | `/milavn/admin/manifest` | Manifest | public / anonymous |  |  | 200 |
| API-002 | GET | `/milavn/admin/members/{member_id}/summary` | Member Summary | moderator (scope milavn.moderate) | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-003 | GET | `/milavn/admin/moderation` | List Queue | moderator (scope milavn.moderate) | status, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-004 | GET | `/milavn/admin/moderation/{item_id}` | Detail | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-005 | POST | `/milavn/admin/moderation/{item_id}/actions/{action_id}` | Act | moderator (scope milavn.moderate) | x-milavn-member-id, x-milavn-language, accept-language | ActionRequest | 200 |

## calendar

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-006 | GET | `/calendar/circle/{circle_id}` | Circle Calendar | signed-in member | start, days, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-007 | GET | `/calendar/community` | Community Calendar | signed-in member | start, days, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-008 | GET | `/calendar/organization/{organization_scope_id}` | Organization Calendar | signed-in member | start, days, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-009 | GET | `/calendar/personal` | Personal | signed-in member | start, days, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-010 | GET | `/calendar/public` | Public Calendar | optional member (public view, richer when signed in) | city*, start, days, x-milavn-member-id |  | 200 |

## chat

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-011 | GET | `/chats` | List Chats | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-012 | GET | `/chats/activity/{occurrence_id}` | Activity Chat | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-013 | POST | `/chats/direct` | Open Direct | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | DirectRequest | 201 |
| API-014 | POST | `/chats/group` | Create Group | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | app__api__routes__chat__GroupRequest | 201 |
| API-015 | GET | `/chats/unread` | Unread | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-016 | GET | `/chats/{conversation_id}` | Get Conversation | signed-in member | after, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-017 | POST | `/chats/{conversation_id}/messages` | Send Message | signed-in member | x-milavn-member-id, x-milavn-language, accept-language, Idempotency-Key | SendRequest | 201 |
| API-018 | DELETE | `/chats/{conversation_id}/messages/{message_id}` | Retract | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |
| API-019 | POST | `/chats/{conversation_id}/messages/{message_id}/reactions` | React | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | ReactionRequest | 200 |
| API-020 | POST | `/chats/{conversation_id}/photos` | Send Photo | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | Body_send_photo_chats__conversation_id__photos_post | 201 |
| API-021 | POST | `/chats/{conversation_id}/read` | Read | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |
| API-022 | POST | `/presence` | Presence | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | PresenceRequest | 204 |

## circle-social

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-023 | GET | `/circles/{circle_id}/albums` | List Albums | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-024 | POST | `/circles/{circle_id}/albums` | Create Album | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | AlbumRequest | 201 |
| API-025 | GET | `/circles/{circle_id}/albums/{album_id}` | Get Album | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-026 | DELETE | `/circles/{circle_id}/albums/{album_id}` | Delete Album | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |
| API-027 | POST | `/circles/{circle_id}/albums/{album_id}/photos` | Add Album Photos | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | Body_add_album_photos_circles__circle_id__albums__album_id__photos_post | 201 |
| API-028 | DELETE | `/circles/{circle_id}/albums/{album_id}/photos/{photo_id}` | Delete Album Photo | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |
| API-029 | GET | `/circles/{circle_id}/cohost-invites` | Circle Cohost Invites | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-030 | POST | `/circles/{circle_id}/cohost-invites/{occurrence_id}/respond` | Respond Cohost | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | CohostResponse | 200 |
| API-031 | GET | `/circles/{circle_id}/notify` | Get Notify | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-032 | PUT | `/circles/{circle_id}/notify` | Put Notify | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | NotifyLevelRequest | 200 |
| API-033 | GET | `/occurrences/{occurrence_id}/cohost-candidates` | Cohost Candidates | signed-in member | q, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-034 | GET | `/occurrences/{occurrence_id}/cohosts` | List Cohosts | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-035 | POST | `/occurrences/{occurrence_id}/cohosts` | Invite Cohost | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | CohostInviteRequest | 201 |
| API-036 | DELETE | `/occurrences/{occurrence_id}/cohosts/{circle_id}` | Remove Cohost | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |

## circles

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-037 | POST | `/circles` | Create | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | CreateCircleRequest | 201 |
| API-038 | GET | `/circles/discover` | Discover | signed-in member | q, near, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-039 | GET | `/circles/gender/me` | My Gender | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-040 | PUT | `/circles/gender/me` | Set My Gender | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | GenderRequest | 200 |
| API-041 | GET | `/circles/groups` | List Groups | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-042 | POST | `/circles/groups` | Create Group | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | app__api__routes__circles__GroupRequest | 201 |
| API-043 | GET | `/circles/groups/{group_id}` | Group Detail | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-044 | GET | `/circles/groups/{group_id}/chapters` | Group Chapters | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-045 | POST | `/circles/groups/{group_id}/updates` | Post Group Update | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | GroupUpdateRequest | 201 |
| API-046 | GET | `/circles/invites/mine` | My Invites | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-047 | POST | `/circles/invites/{invite_id}/respond` | Respond Invite | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | InviteResponse | 200 |
| API-048 | GET | `/circles/join/{token}` | Invite Link Preview | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-049 | POST | `/circles/join/{token}` | Join By Link | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-050 | GET | `/circles/mine` | Mine | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-051 | GET | `/circles/organizations` | Organizations | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-052 | POST | `/circles/organizations` | Create Organization | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | OrgScopeRequest | 201 |
| API-053 | GET | `/circles/recommended` | Recommended | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-054 | GET | `/circles/suggestions` | Suggestions | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-055 | POST | `/circles/suggestions/run` | Run Suggestions | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-056 | POST | `/circles/suggestions/{suggestion_id}/respond` | Respond | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | SuggestionResponse | 200 |
| API-057 | GET | `/circles/types` | Types | public / anonymous |  |  | 200 |
| API-058 | GET | `/circles/{circle_id}` | Detail | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-059 | PATCH | `/circles/{circle_id}` | Update | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | UpdateCircleRequest | 200 |
| API-060 | DELETE | `/circles/{circle_id}` | Delete | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |
| API-061 | POST | `/circles/{circle_id}/cover` | Upload Cover | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | Body_upload_cover_circles__circle_id__cover_post | 200 |
| API-062 | DELETE | `/circles/{circle_id}/cover` | Remove Cover | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-063 | GET | `/circles/{circle_id}/fundraisers` | Circle Fundraisers | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-064 | POST | `/circles/{circle_id}/fundraisers` | Create Fundraiser | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | FundraiserRequest | 201 |
| API-065 | POST | `/circles/{circle_id}/fundraisers/{fundraiser_id}/close` | Close Fundraiser | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |
| API-066 | POST | `/circles/{circle_id}/fundraisers/{fundraiser_id}/paid` | Mark Paid | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | MarkPaidRequest | 200 |
| API-067 | POST | `/circles/{circle_id}/fundraisers/{fundraiser_id}/pledge` | Pledge | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | PledgeRequest | 204 |
| API-068 | GET | `/circles/{circle_id}/fundraisers/{fundraiser_id}/pledges` | Pledge List | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-069 | POST | `/circles/{circle_id}/group` | Attach Group | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | AttachGroupRequest | 200 |
| API-070 | POST | `/circles/{circle_id}/invite-link` | Create Invite Link | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 201 |
| API-071 | POST | `/circles/{circle_id}/invites` | Invite | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | InviteRequest | 200 |
| API-072 | GET | `/circles/{circle_id}/invites` | Circle Invites | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-073 | DELETE | `/circles/{circle_id}/invites/{invite_id}` | Cancel Invite | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |
| API-074 | POST | `/circles/{circle_id}/join` | Join | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | json | 200 |
| API-075 | GET | `/circles/{circle_id}/join-prompt` | Join Prompt | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-076 | POST | `/circles/{circle_id}/leave` | Leave | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-077 | POST | `/circles/{circle_id}/members` | Add Member | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | MemberRefRequest | 201 |
| API-078 | DELETE | `/circles/{circle_id}/members/{member_id}` | Remove Member | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |
| API-079 | GET | `/circles/{circle_id}/polls` | Circle Polls | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-080 | POST | `/circles/{circle_id}/polls` | Create Poll | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | CreatePollRequest | 201 |
| API-081 | POST | `/circles/{circle_id}/polls/{poll_id}/close` | Close Poll | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |
| API-082 | POST | `/circles/{circle_id}/polls/{poll_id}/vote` | Vote In Poll | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | VoteRequest | 204 |
| API-083 | GET | `/circles/{circle_id}/requests` | Join Requests | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-084 | POST | `/circles/{circle_id}/requests/{request_id}/decide` | Decide Join Request | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | DecideRequest | 200 |
| API-085 | POST | `/circles/{circle_id}/roles` | Set Circle Role | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | RoleRequest | 200 |
| API-086 | PUT | `/circles/{circle_id}/trip-plan` | Set Trip Plan | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | TripPlanRequest | 200 |

## conversation

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-087 | GET | `/circles/{circle_id}/posts` | List Posts | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-088 | POST | `/circles/{circle_id}/posts` | Post To Board | signed-in member | x-milavn-member-id, x-milavn-language, accept-language, Idempotency-Key | MessageRequest | 201 |
| API-089 | POST | `/circles/{circle_id}/posts/media` | Post Photo To Board | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | Body_post_photo_to_board_circles__circle_id__posts_media_post | 201 |
| API-090 | DELETE | `/circles/{circle_id}/posts/{post_id}` | Delete Board Post | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |
| API-091 | POST | `/circles/{circle_id}/posts/{post_id}/comments` | Comment On Post | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | CommentRequest | 201 |
| API-092 | DELETE | `/circles/{circle_id}/posts/{post_id}/comments/{comment_id}` | Delete Post Comment | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |
| API-093 | POST | `/circles/{circle_id}/posts/{post_id}/pin` | Pin Board Post | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | PinRequest | 200 |
| API-094 | POST | `/circles/{circle_id}/posts/{post_id}/reactions` | React To Post | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | PostReactionRequest | 200 |
| API-095 | GET | `/moments/preference` | Get Photo Preference | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-096 | PUT | `/moments/preference` | Put Photo Preference | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | PhotoPreference | 200 |
| API-097 | GET | `/occurrences/{occurrence_id}/messages` | List Messages | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-098 | POST | `/occurrences/{occurrence_id}/messages` | Post Message | signed-in member | x-milavn-member-id, x-milavn-language, accept-language, Idempotency-Key | MessageRequest | 201 |
| API-099 | DELETE | `/occurrences/{occurrence_id}/messages/{message_id}` | Delete Message | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |
| API-100 | GET | `/occurrences/{occurrence_id}/photos` | List Photos | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-101 | POST | `/occurrences/{occurrence_id}/photos` | Add Photo | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | Body_add_photo_occurrences__occurrence_id__photos_post | 201 |
| API-102 | DELETE | `/occurrences/{occurrence_id}/photos/{photo_id}` | Delete Photo | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |
| API-103 | POST | `/occurrences/{occurrence_id}/photos/{photo_id}/remove` | Remove Photo Of Me | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |

## discovery

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-104 | GET | `/discovery/around-you` | Around You | signed-in member | lat, lng, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-105 | GET | `/discovery/calendar` | Calendar | signed-in member | date*, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-106 | GET | `/discovery/digest` | Digest | signed-in member | lat, lng, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-107 | POST | `/discovery/hide` | Hide | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | HideRequest | 204 |
| API-108 | GET | `/discovery/map` | Map Mode | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-109 | GET | `/discovery/search` | Search | signed-in member | q, category, scope, when, distance, safe_only, free, audience, food, format, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-110 | GET | `/discovery/smart-fill` | Smart Fill | signed-in member | text*, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-111 | GET | `/discovery/understand` | Understand | signed-in member | q*, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |

## events

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-112 | PUT | `/occurrences/{occurrence_id}/followup` | Put Followup | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | FollowupBody | 200 |
| API-113 | POST | `/occurrences/{occurrence_id}/join-online` | Join Online | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-114 | GET | `/occurrences/{occurrence_id}/program` | Program | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-115 | POST | `/occurrences/{occurrence_id}/sessions` | Add Session | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | SessionBody | 201 |
| API-116 | DELETE | `/occurrences/{occurrence_id}/sessions/{session_id}` | Remove Session | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-117 | POST | `/occurrences/{occurrence_id}/speakers` | Add Speaker | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | SpeakerBody | 201 |
| API-118 | DELETE | `/occurrences/{occurrence_id}/speakers/{speaker_id}` | Remove Speaker | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-119 | POST | `/occurrences/{occurrence_id}/stalls` | Add Stall | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | StallBody | 201 |
| API-120 | DELETE | `/occurrences/{occurrence_id}/stalls/{stall_id}` | Remove Stall | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-121 | POST | `/occurrences/{occurrence_id}/teams` | Register Team | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | TeamBody | 201 |
| API-122 | POST | `/occurrences/{occurrence_id}/teams/{team_id}/join` | Join Team | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-123 | DELETE | `/occurrences/{occurrence_id}/teams/{team_id}/members/{member_id}` | Leave Or Remove | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |

## feedback

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-124 | POST | `/feedback` | Submit | signed-in member | x-milavn-member-id, x-milavn-language, accept-language, Idempotency-Key | FeedbackRequest | 201 |
| API-125 | GET | `/feedback/prompt/{occurrence_id}` | Prompt | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-126 | POST | `/feedback/thanks` | Thank Host | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | ThanksRequest | 201 |

## identity

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-127 | GET | `/identity/dev/members` | Dev Members | public / anonymous |  |  | 200 |
| API-128 | GET | `/identity/me` | Me | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |

## notifications

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-129 | GET | `/notifications` | Inbox | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-130 | GET | `/notifications/preferences` | Get Preferences | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-131 | PUT | `/notifications/preferences` | Set Preference | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | PreferenceRequest | 200 |
| API-132 | POST | `/notifications/read` | Mark All Read | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-133 | GET | `/notifications/unread-count` | Unread | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-134 | DELETE | `/notifications/{entry_id}` | Dismiss | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-135 | POST | `/notifications/{entry_id}/read` | Mark Read | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |

## occurrences

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-136 | POST | `/occurrences` | Create Occurrence | signed-in member | x-milavn-member-id, x-milavn-language, accept-language, Idempotency-Key | CreateOccurrenceRequest | 201 |
| API-137 | GET | `/occurrences/by-slug/{slug}` | Get By Slug | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-138 | POST | `/occurrences/cover` | Upload Cover | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | Body_upload_cover_occurrences_cover_post | 201 |
| API-139 | GET | `/occurrences/mine` | My Occurrences | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-140 | GET | `/occurrences/{occurrence_id}` | Get Occurrence | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-141 | PATCH | `/occurrences/{occurrence_id}` | Update Occurrence | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | UpdateOccurrenceRequest | 200 |
| API-142 | GET | `/occurrences/{occurrence_id}/after` | After The Activity | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-143 | POST | `/occurrences/{occurrence_id}/announcements` | Announce | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | AnnouncementRequest | 201 |
| API-144 | POST | `/occurrences/{occurrence_id}/attendance` | Mark Attendance | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | AttendanceRequest | 200 |
| API-145 | GET | `/occurrences/{occurrence_id}/attendees` | Attendees | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-146 | POST | `/occurrences/{occurrence_id}/cancel` | Cancel Occurrence | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | CancelRequest | 200 |
| API-147 | POST | `/occurrences/{occurrence_id}/checkin` | Checkin | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | CheckinRequest | 200 |
| API-148 | POST | `/occurrences/{occurrence_id}/checkin/token` | Checkin Token | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-149 | POST | `/occurrences/{occurrence_id}/co-organizers` | Grant Co Organizer | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | MemberRefRequest | 201 |
| API-150 | DELETE | `/occurrences/{occurrence_id}/co-organizers/{member_id}` | Revoke Co Organizer | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-151 | POST | `/occurrences/{occurrence_id}/complete` | Complete | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-152 | POST | `/occurrences/{occurrence_id}/confirm` | Confirm Still Coming | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-153 | GET | `/occurrences/{occurrence_id}/conversation-cards` | Conversation Cards | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-154 | POST | `/occurrences/{occurrence_id}/participation` | Set Participation | signed-in member | x-milavn-member-id, x-milavn-language, accept-language, Idempotency-Key | ParticipationRequest | 200 |
| API-155 | PUT | `/occurrences/{occurrence_id}/plan` | Set Attendance Plan | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | PlanRequest | 200 |
| API-156 | POST | `/occurrences/{occurrence_id}/regular` | Keep My Spot | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | RegularRequest | 200 |
| API-157 | POST | `/occurrences/{occurrence_id}/series` | Add Series Occurrence | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | CreateOccurrenceRequest | 201 |

## ops

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-158 | GET | `/health` | Health | public / anonymous (defined in main.py) |  |  | 200 |

## payments

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-159 | GET | `/occurrences/{occurrence_id}/money` | Organizer Money | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-160 | GET | `/occurrences/{occurrence_id}/ticket` | My Ticket | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-161 | POST | `/occurrences/{occurrence_id}/ticket` | Join Paid | signed-in member | x-milavn-member-id, x-milavn-language, accept-language, Idempotency-Key | json | 200 |
| API-162 | POST | `/occurrences/{occurrence_id}/ticket/withdraw` | Withdraw Paid | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-163 | POST | `/payments/events` | Payment Events | public / anonymous | x-forkhatri-service, x-forkhatri-service-key, x-forkhatri-signature | PaymentEvent | 200 |
| API-164 | GET | `/payments/sandbox/{reference}` | Sandbox Checkout | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-165 | POST | `/payments/sandbox/{reference}/complete` | Sandbox Complete | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | SandboxOutcome | 200 |
| API-166 | GET | `/tickets/mine` | Tickets Mine | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |

## people

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-167 | GET | `/people/connections` | Connections | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-168 | GET | `/people/free-now` | Free Now | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-169 | POST | `/people/free-now` | Set Free Now | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | FreeNowRequest | 200 |
| API-170 | DELETE | `/people/free-now` | Clear Free Now | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 204 |
| API-171 | POST | `/people/meet-again` | Meet Again | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | MeetAgainRequest | 200 |
| API-172 | GET | `/people/meet-again/{occurrence_id}` | Meet Again Candidates | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-173 | GET | `/people/reputation/{member_id}` | Reputation | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-174 | GET | `/people/search` | Search People | signed-in member | q, circle_id, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-175 | GET | `/people/suggestions` | Suggestions | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-176 | GET | `/people/{member_id}` | Public Profile | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-177 | POST | `/people/{member_id}/follow` | Follow Host | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | FollowRequest | 200 |

## privacy

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-178 | GET | `/privacy/location` | Get Location Privacy | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-179 | PUT | `/privacy/location` | Set Location Privacy | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | PrecisionRequest | 200 |

## profile

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-180 | POST | `/profile` | Save Onboarding | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | OnboardingRequest | 201 |
| API-181 | PATCH | `/profile/enrichment` | Update Enrichment | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | Body_update_enrichment_profile_enrichment_patch | 200 |
| API-182 | PUT | `/profile/interests` | Set Interests | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | InterestsRequest | 200 |
| API-183 | GET | `/profile/interests/taxonomy` | Interests Taxonomy | public / anonymous |  |  | 200 |
| API-184 | PATCH | `/profile/language` | Set Language | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | LanguageRequest | 200 |
| API-185 | GET | `/profile/me` | Get Me | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-186 | PATCH | `/profile/place` | Set Place | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | PlaceRequest | 200 |
| API-187 | GET | `/profile/places` | Search Places | signed-in member | q, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-188 | GET | `/profile/places/nearest` | Nearest Place | signed-in member | lat*, lng*, x-milavn-member-id, x-milavn-language, accept-language |  | 200 |

## public

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-189 | GET | `/public/hosts/{host_member_id}/calendar.ics` | Host Calendar Feed | public / anonymous |  |  | 200 |
| API-190 | GET | `/public/occurrences/{slug}` | Public Occurrence | optional member (public view, richer when signed in) | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |

## safety

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-191 | POST | `/safety/blocks` | Block | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | BlockRequest | 201 |
| API-192 | GET | `/safety/blocks` | My Blocks | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-193 | DELETE | `/safety/blocks/{member_id}` | Unblock | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-194 | POST | `/safety/reports` | Submit Report | signed-in member | x-milavn-member-id, x-milavn-language, accept-language, Idempotency-Key | ReportRequest | 201 |
| API-195 | GET | `/safety/reports/mine` | My Reports | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |

## tickets

| ID | Method | Path | Summary | Auth | Query | Body schema | Status codes |
|---|---|---|---|---|---|---|---|
| API-196 | POST | `/occurrences/{occurrence_id}/checkin/ticket` | Checkin Ticket | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | CheckinTicketBody | 200 |
| API-197 | PUT | `/occurrences/{occurrence_id}/contact` | Put Contact | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | ContactBody | 200 |
| API-198 | POST | `/occurrences/{occurrence_id}/discount-codes` | Add Discount Code | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | DiscountCodeBody | 201 |
| API-199 | PATCH | `/occurrences/{occurrence_id}/discount-codes/{code_id}` | Toggle Discount Code | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | DiscountActiveBody | 200 |
| API-200 | GET | `/occurrences/{occurrence_id}/ticket-admin` | Ticket Admin | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-201 | POST | `/occurrences/{occurrence_id}/ticket-types` | Add Ticket Type | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | TicketTypeBody | 201 |
| API-202 | PATCH | `/occurrences/{occurrence_id}/ticket-types/{type_id}` | Edit Ticket Type | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | TicketTypeBody | 200 |
| API-203 | DELETE | `/occurrences/{occurrence_id}/ticket-types/{type_id}` | Remove Ticket Type | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |
| API-204 | POST | `/occurrences/{occurrence_id}/ticket/quote` | Ticket Quote | signed-in member | x-milavn-member-id, x-milavn-language, accept-language | QuoteRequest | 200 |
| API-205 | GET | `/occurrences/{occurrence_id}/ticketing` | Event Ticketing | signed-in member | x-milavn-member-id, x-milavn-language, accept-language |  | 200 |

## Internal and non-OpenAPI

| ID | Method | Path | Notes |
|---|---|---|---|
| API-206 | GET | `/internal/v1/insights/members` | Platform-only aggregate member insights for the ForKhatri dashboard; guarded by the platform service key (`platform_caller`), `include_in_schema=False`. |
| API-207 | WS | `/ws/chat` | Chat WebSocket (presence, typing, new messages, reactions); session cookie authenticated by `resolve_member_identity`. |
| API-208 | GET | `/media/*` | Public static media (cover images etc.); private folders refused by the mount and served by gated routes in `media.py`. |
| API-209 | GET/HEAD | `/media/circle-posts/{name}` | Circle post photo; served only to circle members (RLS check via `circle_media_access`). |
| API-210 | GET/HEAD | `/media/circle-docs/{name}` | Circle post document (pdf/doc/xls/ppt/txt); members only, 404 to others. |
| API-211 | GET/HEAD | `/media/circle-albums/{name}` | Circle album photo; members only. |
| API-212 | GET/HEAD | `/media/circle-covers/{name}?invite=` | Circle cover; members, or anyone holding a valid invite token. |
| API-213 | GET/HEAD | `/media/chat/{name}` | Chat photo; conversation members only. |
| API-214 | GET/HEAD | `/media/moments/{name}` | Moments photo; people who were at the activity only. |


## Added 2026-11-22: account deletion
| ID | Method | Path | Notes |
|---|---|---|---|
| API-215 | POST | `/privacy/delete-account-data` | Kind B. Signed-in member. Body `{"confirm":"DELETE"}`. 200 contract JSON (`status`, `deleted`, `retained`, `files_removed`); 422 wrong word; 429 after 3 per hour (Retry-After); 503 if a refund cannot be requested (nothing deleted). In OpenAPI (206 operations now). |
| API-216 | POST | `/internal/v1/members/{member_id}/erase` | Kind A. Service key `X-ForKhatri-Service-Key` (hub also sends `X-ForKhatri-Service: identity`); 401 without it; not in OpenAPI. 200 `{module:"milavn", status: done / nothing_to_delete / partial, deleted, retained, files_removed}`; idempotent. |

The hub's own endpoints (`/v1/account/delete/*`, `/v1/admin/deletions/*`) are in the identity service reference, not here.
