package com.manas.skill.domain;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;

@Entity
public class ServiceRequest {

    @Id
    private String id;

    @Lob
    private String text;

    /** Null for requests built from out-of-corpus vocabulary; these have no resolvable article. */
    private String trueArticleId;

    private boolean groundedByConstruction;

    public ServiceRequest() {
    }

    public ServiceRequest(String id, String text, String trueArticleId, boolean groundedByConstruction) {
        this.id = id;
        this.text = text;
        this.trueArticleId = trueArticleId;
        this.groundedByConstruction = groundedByConstruction;
    }

    public String getId() {
        return id;
    }

    public String getText() {
        return text;
    }

    public String getTrueArticleId() {
        return trueArticleId;
    }

    public boolean isGroundedByConstruction() {
        return groundedByConstruction;
    }
}
