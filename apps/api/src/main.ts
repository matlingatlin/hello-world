import { ValidationPipe } from "@nestjs/common";
import { NestFactory } from "@nestjs/core";
import { DocumentBuilder, SwaggerModule } from "@nestjs/swagger";
import { AppModule } from "./app.module";

/**
 * Which browser origins may call this API.
 *
 * An allow list, never a wildcard, and empty by default: the api is only ever
 * reached cross-origin by the app, so naming that origin is one line of config
 * rather than a hole left open. Found by the first local click-through — every
 * test until then called the api in-process, where CORS does not exist, so the
 * product could not load a single project in a real browser.
 */
function corsOrigins(): string[] {
  return (process.env.CORS_ORIGINS ?? "")
    .split(",")
    .map((origin) => origin.trim())
    .filter(Boolean);
}

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));

  const origins = corsOrigins();
  if (origins.length > 0) {
    app.enableCors({ origin: origins, credentials: true });
  }

  const config = new DocumentBuilder()
    .setTitle("Scio API")
    .setDescription(
      "Typed API contract for the Scio backend. Skeleton stage — shapes and stubs; business logic lands in phases 3.3+.",
    )
    .setVersion("0.0.1")
    .build();
  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup("docs", app, document);

  const port = Number(process.env.PORT ?? 3000);
  await app.listen(port);
}

void bootstrap();
