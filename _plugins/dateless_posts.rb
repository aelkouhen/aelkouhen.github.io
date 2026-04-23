# Allow posts in _posts/ to omit the date from their filename.
# Jekyll normally requires YYYY-MM-DD- prefix; this plugin removes that constraint.
# Each post must supply `date:` in its frontmatter instead.

module Jekyll
  class PostReader
    DATELESS_POST_MATCHER = %r!\.(md|markdown|html)$!

    def read_posts(dir)
      read_publishable(dir, "_posts", DATELESS_POST_MATCHER)
    end
  end
end
