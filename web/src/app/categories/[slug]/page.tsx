import { Suspense } from "react";
import { CategoryView } from "./category-view";

export default function CategoryPage({ params }: PageProps<"/categories/[slug]">) {
  return (
    <Suspense fallback={<div className="mx-auto max-w-[1240px] px-5 py-10 sm:px-8" />}>
      <CategoryView params={params} />
    </Suspense>
  );
}
