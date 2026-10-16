# Authentication & Authorization

## Auth Strategy

We decided to implement **JWT-based stateless authentication** instead of server-side 
sessions. The key reason: our API needs to support both web and mobile clients, and 
session state on the server would complicate horizontal scaling. Redis-backed sessions 
were considered but add operational overhead we don't need yet.

JWT access tokens expire in 15 minutes; refresh tokens last 7 days and are rotated 
on each use.

## Password Hashing

**bcrypt** was chosen over Argon2 and PBKDF2. Argon2 is theoretically stronger but 
has less battle-tested library support in our Python ecosystem. PBKDF2 was rejected 
as too weak against GPU attacks. bcrypt hits the right balance of security and 
library maturity.

## OAuth Providers

We chose to support **Google and GitHub OAuth** only (via authlib), and rejected 
Facebook OAuth. The decision was based on our target audience (developers), who 
overwhelmingly use Google or GitHub. Supporting Facebook would add surface area 
with minimal user benefit.

## Role System

A simple **RBAC (Role-Based Access Control)** model was chosen over ABAC 
(Attribute-Based). ABAC was considered but deemed over-engineered for our current 
requirements. We have three roles: admin, member, viewer. This can be extended to 
ABAC later if needed.

## API Rate Limiting

**Redis-based rate limiting** (sliding window) was chosen over in-memory limiting. 
In-memory limits don't survive restarts and break with multiple server instances. 
Redis gives us a shared counter across all instances.
