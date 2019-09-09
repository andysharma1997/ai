# Signal Engine

A signal engine in our world is a multi-label classifier which when passed a text with a bunch of other texts grouped into categories, assigns a category to the text. We are going to try a few algorithms here.

## SVM

The first algorithm we are going for is a support vector machine. We are using USE embedding as the vector space. USE can be applied at word, phrase and paragraph levels. At the same time we are not going to get a lot of input signals. Put in combination we get a suitable setup for our scenarion which struggles from these limitations:
 * Less training samples
 * Variable input length
At the same time using a simplistic algorithm like SVM and a quick embedder like USE will satisfy the low computation requirement and the voluminous throughput we are looking for.
