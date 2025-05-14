---
layout: default
title: Blog
---

<h2>📝 Blog</h2>

<ul>
  {% for post in site.posts %}
    <li>
      <a href="{{ post.url }}">{{ post.title }}</a>
      <span>({{ post.date | date: "%d/%m/%Y" }})</span>
    </li>
  {% endfor %}
</ul>
