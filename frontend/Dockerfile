# ---- build ----
FROM node:20-slim AS build
WORKDIR /ui
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# ---- serve with nginx ----
FROM nginx:1.27-alpine
COPY --from=build /ui/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
