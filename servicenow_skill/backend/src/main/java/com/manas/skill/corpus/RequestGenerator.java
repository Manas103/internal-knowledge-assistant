package com.manas.skill.corpus;

import com.manas.skill.domain.KnowledgeArticle;
import com.manas.skill.domain.ServiceRequest;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Generates the frozen held-out evaluation set: requests grounded in a real article's own
 * vocabulary, plus requests built entirely from an out-of-corpus vocabulary pool (facilities and
 * HR topics an IT knowledge base never covers) that no article can resolve. The ungrounded count
 * is fixed at {@link #UNGROUNDED_COUNT} so the withhold rate is a known, checkable number.
 */
public final class RequestGenerator {

    public static final int GROUNDED_COUNT = 457;
    public static final int UNGROUNDED_COUNT = 148;
    public static final int TOTAL_COUNT = GROUNDED_COUNT + UNGROUNDED_COUNT;

    /** Facilities and HR phrasing an IT knowledge base never covers; deliberately checked against TOPIC_KEYWORDS and FILLER for zero token overlap (see CorpusGeneratorTest). */
    private static final List<String> OUT_OF_CORPUS_VOCAB = List.of(
            "cafeteria-lunch-menu", "visitor-parking-pass", "gym-locker-key",
            "snack-bar-restock", "bike-rack-location", "office-plant-watering",
            "lost-umbrella-bin", "birthday-cake-delivery", "carpool-rideshare-list",
            "thermostat-temperature-complaint", "elevator-inspection-sticker", "courier-package-dropoff",
            "rooftop-garden-volunteer", "foosball-paddle-replacement", "potluck-dish-signup");

    private RequestGenerator() {
    }

    public static List<ServiceRequest> generate(List<KnowledgeArticle> corpus, long seed) {
        Random random = new Random(seed);
        List<ServiceRequest> requests = new ArrayList<>(TOTAL_COUNT);

        for (int i = 0; i < GROUNDED_COUNT; i++) {
            KnowledgeArticle article = corpus.get(random.nextInt(corpus.size()));
            List<String> keywords = CorpusGenerator.TOPIC_KEYWORDS.get(article.getTopic());
            String kw1 = keywords.get(random.nextInt(keywords.size())).replace('-', '_');
            String kw2 = keywords.get(random.nextInt(keywords.size())).replace('-', '_');
            String text = "A user on " + article.getPlatform() + " at " + article.getSite()
                    + " reports trouble with " + kw1 + " and asks for help with " + kw2
                    + " related to " + article.getTopic().replace('-', '_') + ".";
            requests.add(new ServiceRequest("REQ-G-" + String.format("%04d", i), text, article.getId(), true));
        }

        for (int i = 0; i < UNGROUNDED_COUNT; i++) {
            String phrase = OUT_OF_CORPUS_VOCAB.get(random.nextInt(OUT_OF_CORPUS_VOCAB.size())).replace('-', ' ');
            String phrase2 = OUT_OF_CORPUS_VOCAB.get(random.nextInt(OUT_OF_CORPUS_VOCAB.size())).replace('-', ' ');
            String text = "A user asks about " + phrase + " and mentions " + phrase2 + " in the same request.";
            requests.add(new ServiceRequest("REQ-U-" + String.format("%04d", i), text, null, false));
        }

        return requests;
    }
}
