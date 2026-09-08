# Publishing the report site on Pages

The site is the easy part. It is plain files: no build step, no framework, no runtime, no
environment variables. Any static host serves it.

## Deploy

```sh
npx wrangler pages project create <your-project> --production-branch main
npx wrangler pages deploy <path-to-site-repo> --project-name <your-project>
```

Or connect the site repository in the dashboard and let a push deploy it. Set the build command
to empty and the output directory to the repository root: there is nothing to build, and a
framework preset guessing otherwise is the most likely way to break this.

## Two host requirements, and only two

**Serve the media content types correctly.** Reports embed JSON, MP3 and MP4 by relative path.
Pages handles these, but if you put a proxy in front, check them.

**Do not run a static-site generator over the output.** The pages are already rendered. On
GitHub Pages this needs an explicit opt-out file; on Pages it is the default, so there is
nothing to do beyond not configuring one.

## Headers

Add a `_headers` file for cache behaviour. Content-addressed assets are immutable, so they can
be cached hard. The index and roll-up change on every publish.

```
/reports/*/assets/*
  Cache-Control: public, max-age=31536000, immutable

/index.html
  Cache-Control: public, max-age=300

/site-data.json
  Cache-Control: public, max-age=300
```

## Where the media lives

Two options, and the first is usually right.

**In the repository.** Assets are bundled into the report directory at publish time and
committed. The site is self-contained, a clone is a full backup, and there is no second system
to keep in step. The reference deployment does this and reached 99 MB across 14 reports, which
is unremarkable.

**In R2, referenced by URL.** Worth it once repository size becomes a real problem, typically
past a few gigabytes. The cost is that a report is no longer self-contained: an asset can be
deleted out from under a published page, and nothing in the publish gate will notice. If you do
this, keep the bundle verification step and point it at R2, or you lose the guarantee that
every reference in a published page resolves.

Do not mix the two. A site where some reports are self-contained and others are not is one
where nobody can say what a backup contains.

## What not to put here

No model code, no configuration, no credentials, no infrastructure detail. This is a public
artifact and the redaction gate exists because the leak that matters is the one nobody meant to
write. See [../../PUBLISHING.md](../../reference/PUBLISHING.md).

Keeping code out is also what keeps copyleft and responsible-use licence terms from attaching
to the published pages. That is not incidental; it is the reason the split exists.

## Verdict capture

The review layer in the reference deployment is browser-local: verdicts go to `localStorage`
and a person exports them as JSON. Nothing is transmitted, which is what lets the site say it
runs no server, accepts no input, stores no accounts and sets no cookies.

D1 plus a Function would let readers submit verdicts directly, and that is a genuinely useful
upgrade. It is also a different privacy posture, a moderation problem, and a new place for
personal data to accumulate. Make it a deliberate decision with its own notice, not a side
effect of having a database available.
