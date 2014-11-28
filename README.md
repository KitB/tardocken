tardocken
==========

Originally forked from [itsafire/dockerfeed](https://github.com/itsafire/dockerfeed), my usage required fairly different
patterns for use so I'm forking it.

tardocken allows you to insert additional context into an existing context for a Dockerfile. It's probably not a very
good idea.

```
usage: tardocken [-h] [-p PATH] [-d DOCKERFILE] [-i DOCKERIGNORE] context

Replace Dockerfile and/or replace file path in context

positional arguments:
  context               path to context

optional arguments:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  Path to insert into context, e.g.
                        extra_context:where_to_put_it
  -d DOCKERFILE, --dockerfile DOCKERFILE
                        replacement dockerfile
  -i DOCKERIGNORE, --dockerignore DOCKERIGNORE
                        A file containing glob rules for which files to
                        exclude from the context. .dockerignore will be used
                        by default if it exists.
```
