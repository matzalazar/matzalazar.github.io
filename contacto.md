---
title: contacto
layout: page
permalink: /contacto
---

<div class="contact-container">
  <h1 class="page-title">Hablemos</h1>
  <p class="contact-intro">Si tenés un desafío técnico, una idea de producto o necesitás optimizar procesos de negocio, escribime y vemos cómo puedo ayudarte.</p>

  <!-- La clase pageclip-form es requerida para que el JS intercepte el envío -->
  <form action="https://send.pageclip.co/hjTP8XjJFTT3wxOr5tmiVcAwakUy6Ca6" class="pageclip-form" method="post">
    <div class="form-group">
      <label for="name">Nombre</label>
      <input type="text" name="name" id="name" required placeholder="Tu nombre" />
    </div>

    <div class="form-group">
      <label for="email">Email</label>
      <input type="email" name="email" id="email" required placeholder="tu@email.com" />
    </div>

    <div class="form-group">
      <label for="message">Mensaje</label>
      <textarea name="message" id="message" required placeholder="¿En qué puedo ayudarte?" rows="5"></textarea>
    </div>

    <div class="form-actions">
      <button type="submit" class="pageclip-form__submit">
        <span>Enviar mensaje</span>
      </button>
    </div>
  </form>
</div>
