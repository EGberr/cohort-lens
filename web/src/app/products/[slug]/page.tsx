import { Suspense } from "react";
import { ProductView } from "./product-view";

export default function ProductPage({ params }: PageProps<"/products/[slug]">) {
  return (
    <Suspense fallback={<div className="mx-auto max-w-[1320px] px-5 py-10 sm:px-8" />}>
      <ProductView params={params} />
    </Suspense>
  );
}
