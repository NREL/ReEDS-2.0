import { ImageBase, ImageBaseView, ImageDataBase } from "./image_base";
import { StackColorMapper } from "../mappers/stack_color_mapper";
import { NDArrayType } from "../../core/util/ndarray";
import * as p from "../../core/properties";
export type ImageStackData = ImageDataBase;
export interface ImageStackView extends ImageData {
}
export declare class ImageStackView extends ImageBaseView {
    model: ImageStack;
    visuals: ImageStack.Visuals;
    connect_signals(): void;
    get image_dimension(): number;
    protected _update_image(): void;
    protected _flat_img_to_buf8(img: NDArrayType<number>): Uint8ClampedArray;
}
export declare namespace ImageStack {
    type Attrs = p.AttrsOf<Props>;
    type Props = ImageBase.Props & {
        color_mapper: p.Property<StackColorMapper>;
    };
    type Visuals = ImageBase.Visuals;
}
export interface ImageStack extends ImageStack.Attrs {
}
export declare class ImageStack extends ImageBase {
    properties: ImageStack.Props;
    __view_type__: ImageStackView;
    constructor(attrs?: Partial<ImageStack.Attrs>);
}
//# sourceMappingURL=image_stack.d.ts.map