---
layout: default
---

## 📝 Blog

<ul>
  {% for post in site.posts %}
    <li>
      <a href="{{ post.url }}">{{ post.title }}</a>
      <span>({{ post.date | date: "%d/%m/%Y" }})</span>
    </li>
  {% endfor %}
</ul>
