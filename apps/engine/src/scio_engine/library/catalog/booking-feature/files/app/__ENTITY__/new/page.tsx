import { __ENTITY_PASCAL__Form } from "@/components/__ENTITY__-form";

export default function New__ENTITY_PASCAL__Page() {
  return (
    <section
      data-scio-id="__ENTITY__-new-page"
      className="mx-auto flex max-w-lg flex-col gap-6 p-6"
    >
      <h1 data-scio-id="__ENTITY__-new-heading" className="text-2xl font-semibold">
        Book a table
      </h1>
      <__ENTITY_PASCAL__Form />
    </section>
  );
}
