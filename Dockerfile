FROM ruby:3.1-slim

WORKDIR /site

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar Gemfile
COPY Gemfile* ./

# Instalar gems
RUN bundle install

# Copiar el resto del sitio
COPY . .

# Exponer puerto
EXPOSE 4000

# Comando por defecto para servir el sitio
CMD ["bundle", "exec", "jekyll", "serve", "--host", "0.0.0.0", "--livereload", "--force_polling"]
