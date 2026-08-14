import { __ENTITY_PASCAL__List } from "@/components/__ENTITY__-list";
import { isConfigured, listOpen__ENTITY_PASCAL__ } from "@/lib/db/__ENTITY__";

export default async function __ENTITY_PASCAL__Page() {
  const rows = await listOpen__ENTITY_PASCAL__();
  const ready = isConfigured();

  return (
    <section data-scio-id="__ENTITY__-page" className="mx-auto flex max-w-2xl flex-col gap-6 p-6">
      <h1 data-scio-id="__ENTITY__-page-heading" className="text-2xl font-semibold">
        Your __ENTITY_PLURAL__
      </h1>
      <a data-scio-id="__ENTITY__-page-new-link" href="/__ENTITY__/new" className="text-sm underline">
        Make a new __ENTITY__
      </a>
      {ready ? null : (
        <p data-scio-id="__ENTITY__-page-no-database" className="text-sm opacity-70">
          Connect a database to start saving __ENTITY_PLURAL__.
        </p>
      )}
      <__ENTITY_PASCAL__List rows={rows} />
    </section>
  );
}
