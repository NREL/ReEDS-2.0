import { Document } from "../document";
import { View, ViewManager } from "../core/view";
import { EmbedTarget } from "./dom";
export declare const index: {
    [key: string]: View;
};
export declare function add_document_standalone(document: Document, element: EmbedTarget, roots?: (EmbedTarget | null)[], use_for_title?: boolean): Promise<ViewManager>;
//# sourceMappingURL=standalone.d.ts.map