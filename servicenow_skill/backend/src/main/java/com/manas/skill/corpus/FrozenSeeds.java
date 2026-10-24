package com.manas.skill.corpus;

/** Fixed seeds so the corpus and the held-out eval set are reproducible bit-for-bit across runs. */
public final class FrozenSeeds {

    public static final long CORPUS_SEED = 42L;
    public static final long REQUEST_SEED = 7L;

    private FrozenSeeds() {
    }
}
