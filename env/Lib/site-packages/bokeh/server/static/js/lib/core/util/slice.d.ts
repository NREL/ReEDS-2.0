import { Serializable, Serializer, serialize, SliceRep } from "../serialization";
export declare class Slice implements Serializable {
    readonly start: number | null;
    readonly stop: number | null;
    readonly step: number | null;
    constructor({ start, stop, step }?: {
        start?: number | null;
        stop?: number | null;
        step?: number | null;
    });
    [serialize](serializer: Serializer): SliceRep;
}
//# sourceMappingURL=slice.d.ts.map