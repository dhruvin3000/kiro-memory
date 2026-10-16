# API Design

## API Style

We decided on **REST over GraphQL**. GraphQL was seriously evaluated but rejected 
because our API consumers are internal teams only, our data graph is shallow, and 
the added complexity of a GraphQL layer (resolvers, N+1 problem, schema stitching) 
isn't justified. We may revisit if we open up a public API.

## Versioning Strategy

**URL path versioning** (/api/v1/) was chosen over header-based versioning. 
Header versioning (Accept: application/vnd.api+json;version=1) is harder to test 
in browsers and cURL. Path versioning is explicit and universally understood.

## Serialization Format

**JSON** is the standard. MessagePack was considered for internal service-to-service 
calls but rejected — the performance gains don't outweigh the debugging difficulty 
when you can't read payloads as plain text.

## Pagination

We use **cursor-based pagination** instead of offset/limit. Offset pagination breaks 
when records are inserted or deleted mid-page. Cursor pagination is stable and scales 
better for large datasets. The cursor is an opaque base64-encoded string of the last 
record's sort key.

## Error Format

All errors follow the **RFC 7807 Problem Details** format:
```json
{
  "type": "https://example.com/errors/not-found",
  "title": "Resource not found",
  "status": 404,
  "detail": "User with id 42 does not exist"
}
```
This was chosen over custom error envelopes so clients have a standard they can 
rely on without reading our docs first.

## Async Task Queue

**Celery with Redis broker** was chosen over RQ and Dramatiq. RQ is simpler but 
has fewer features (no chaining, no canvas). Dramatiq is newer with less community 
support. Celery is battle-tested and our team is familiar with it.
