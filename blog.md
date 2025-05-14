---
layout: default
title: Blog
---

<h1>📝 Blog</h1>

<ul>
  {% for post in site.posts %}
    <li>
      <a href="{{ post.url }}">{{ post.title }}</a>
      <span>({{ post.date | date: "%d/%m/%Y" }})</span>
    </li>
  {% endfor %}
</ul>
