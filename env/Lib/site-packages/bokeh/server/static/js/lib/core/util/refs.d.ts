import { Attrs } from "../types";
export type Struct = {
    id: string;
    type: string;
    attributes: Attrs;
};
export type Ref = {
    id: string;
};
export declare function is_ref(obj: unknown): obj is Ref;
//# sourceMappingURL=refs.d.ts.map