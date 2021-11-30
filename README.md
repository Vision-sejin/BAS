##  Background Activation Suppression for Weakly Supervised Object Localization
xxx
# Overview of BAS
Weakly supervised object localization (WSOL) aims to localize the object region using only image-level labels as supervision. Recently a new paradigm has emerged by generating a foreground prediction map (FPM) to achieve the localization task. Existing FPM-based methods use cross-entropy (CE) to evaluate the foreground prediction map and to guide the learning of generator. We argue for using activation value to achieve more efficient learning. It is based on the experimental observation that, for a trained network, CE converges to zero when the foreground mask covers only part of the object region. While activation value increases until the mask expands to the object boundary, which indicates that more object areas can be learned by using activation value. In this paper, we propose a Background Activation Suppression (BAS) method. Specifically, an Activation Map Constraint module (AMC) is designed to facilitate the learning of generator by suppressing the background activation values. Meanwhile, by using the foreground region guidance and the area constraint, BAS can learn the whole region of the object. Furthermore, in the inference phase, we consider the prediction maps of different categories together to obtain the final localization results. Extensive experiments show that BAS achieves significant and consistent improvement over the baseline methods on the CUB-200-2011 and ILSVRC datasets.
