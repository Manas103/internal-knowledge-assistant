package com.manas.skill.domain;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;

@Entity
public class KnowledgeArticle {

    @Id
    private String id;

    private String topic;

    private String title;

    @Lob
    private String body;

    private String platform;

    private String site;

    public KnowledgeArticle() {
    }

    public KnowledgeArticle(String id, String topic, String title, String body, String platform, String site) {
        this.id = id;
        this.topic = topic;
        this.title = title;
        this.body = body;
        this.platform = platform;
        this.site = site;
    }

    public String getId() {
        return id;
    }

    public String getTopic() {
        return topic;
    }

    public String getTitle() {
        return title;
    }

    public String getBody() {
        return body;
    }

    public String getPlatform() {
        return platform;
    }

    public String getSite() {
        return site;
    }
}
