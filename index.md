---
title: /home
layout: home
permalink: /
---

Hola.

Soy Matías y vivo en Bahía Blanca, Argentina.

**Ciberseguridad**, **automatización** <a href="#footnote-auto" class="footnote-ref">*</a> y **ciencia de datos**.  

Con **Python**, para hacer más con menos.  

{% assign reading_items = site.data.reading %}
{% if reading_items and reading_items != empty %}
  {% capture contenido_lectura %}
  <div id="ahora-leyendo">
    ¿Qué estoy leyendo?
    <ul>
    {% for b in reading_items limit:3 %}
      <li>
        {{ b.titulo }} de {% if b.autor %} {{ b.author }}{% endif %}
        {% if b.progress %} ({{ b.progress }}%){% endif %}
      </li>
    {% endfor %}
    </ul>
    <p class="box-link-footer"><a href="https://www.goodreads.com/matzalazar">Goodreads →</a></p>
  </div>
  {% endcapture %}
  {% include box.html content=contenido_lectura %}
{% endif %}

{% assign studies = site.data.studies %}
{% if studies.coursera or studies.upso.en_curso %}
  {% capture contenido_estudios %}
  <div id="estudios">
    ¿Qué estoy estudiando?
    <ul>
    {% for s in studies.coursera %}
      <li>
        {{ s.title }} — ({{ s.percent }}%)
      </li>
    {% endfor %}

    {% for s in studies.upso.en_curso %}
      <li>
        {{ s.nombre | capitalize }} — ({{ s.estado }})
      </li>
    {% endfor %}
    </ul>
    <p class="box-link-footer"><a href="/about">Más sobre mí →</a></p>
  </div>
  {% endcapture %}
  {% include box.html content=contenido_estudios %}
{% endif %}

{% assign work_data = site.data.work %}

{% if work_data and work_data.commits %}
  
  {% capture contenido_github %}
  
  {% assign total_commits = work_data.commits %}
  {% assign total_repos = work_data.repos %}

  <div id="github">
    
    ¿En qué estoy trabajando?
    
    <p>
      **{{ total_commits }}** commits en **{{ total_repos }}** repositorios.
    </p>

    <p class="box-link-footer"><a href="https://github.com/matzalazar">Github →</a></p>
  </div>

  {% endcapture %}
  
  {% include box.html content=contenido_github %}

{% endif %}