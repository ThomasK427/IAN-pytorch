import os
import ast
import spacy
import numpy as np
from errno import ENOENT
from collections import Counter

nlp = spacy.load("en")

def get_data_info(dataset, pre_processed):
    train_fname = dataset + 'train.txt'
    test_fname = dataset + 'test.txt'
    save_fname = dataset + 'data_info.txt'

    word2id, max_aspect_len, max_context_len = {}, 0, 0
    word2id['<pad>'] = 0
    if pre_processed:
        if not os.path.isfile(save_fname):
            raise IOError(ENOENT, 'Not a file', save_fname)
        with open(save_fname, 'r') as f:
            for line in f:
                content = line.strip().split()
                if len(content) == 3:
                    max_aspect_len = int(content[1])
                    max_context_len = int(content[2])
                else:
                    word2id[content[0]] = int(content[1])
    else:
        if not os.path.isfile(train_fname):
            raise IOError(ENOENT, 'Not a file', train_fname)
        if not os.path.isfile(test_fname):
            raise IOError(ENOENT, 'Not a file', test_fname)

        words = []

        lines = open(train_fname, 'r').readlines()
        for i in range(0, len(lines), 3):
            sptoks = nlp(lines[i].strip())
            words.extend([sp.text.lower() for sp in sptoks])
            if len(sptoks) - 1 > max_context_len:
                max_context_len = len(sptoks) - 1
            sptoks = nlp(lines[i + 1].strip())
            if len(sptoks) > max_aspect_len:
                max_aspect_len = len(sptoks)
            words.extend([sp.text.lower() for sp in sptoks])
        word_count = Counter(words).most_common()
        for word, _ in word_count:
            if word not in word2id and ' ' not in word and '\n' not in word and 'aspect_term' not in word:
                word2id[word] = len(word2id)

        lines = open(test_fname, 'r').readlines()
        for i in range(0, len(lines), 3):
            sptoks = nlp(lines[i].strip())
            words.extend([sp.text.lower() for sp in sptoks])
            if len(sptoks) - 1 > max_context_len:
                max_context_len = len(sptoks) - 1
            sptoks = nlp(lines[i + 1].strip())
            if len(sptoks) > max_aspect_len:
                max_aspect_len = len(sptoks)
            words.extend([sp.text.lower() for sp in sptoks])
        word_count = Counter(words).most_common()
        for word, _ in word_count:
            if word not in word2id and ' ' not in word and '\n' not in word and 'aspect_term' not in word:
                word2id[word] = len(word2id)

        with open(save_fname, 'w') as f:
            f.write('length %s %s\n' % (max_aspect_len, max_context_len))
            for key, value in word2id.items():
                f.write('%s %s\n' % (key, value))

    print('There are %s words in the dataset, the max length of aspect is %s, and the max length of context is %s' % (
    len(word2id), max_aspect_len, max_context_len))
    return word2id, max_aspect_len, max_context_len


def read_data(word2id, max_aspect_len, max_context_len, dataset, pre_processed):
    fname = dataset + '.txt'
    save_fname = dataset + '.npz'

    if pre_processed:
        if not os.path.isfile(save_fname):
            raise IOError(ENOENT, 'Not a file', save_fname)
        return save_fname
    else:
        aspects, contexts, labels, aspect_lens, context_lens = list(), list(), list(), list(), list()
        if not os.path.isfile(fname):
            raise IOError(ENOENT, 'Not a file', fname)
        lines = open(fname, 'r').readlines()
        for i in range(0, len(lines), 3):
            polarity = lines[i + 2].split()[0]
            if polarity == 'conflict':
                continue

            context_sptoks = nlp(lines[i].strip())
            context = []
            for sptok in context_sptoks:
                if sptok.text.lower() in word2id:
                    context.append(word2id[sptok.text.lower()])

            aspect_sptoks = nlp(lines[i + 1].strip())
            aspect = []
            for aspect_sptok in aspect_sptoks:
                if aspect_sptok.text.lower() in word2id:
                    aspect.append(word2id[aspect_sptok.text.lower()])

            aspects.append(aspect + [0] * (max_aspect_len - len(aspect)))
            contexts.append(context + [0] * (max_context_len - len(context)))
            if polarity == 'negative':
                labels.append(0)
            elif polarity == 'neutral':
                labels.append(1)
            elif polarity == 'positive':
                labels.append(2)
            aspect_lens.append(len(aspect_sptoks))
            context_lens.append(len(context_sptoks) - 1)
        print("Read %s examples from %s" % (len(aspects), fname))
        aspects = np.asarray(aspects)
        contexts = np.asarray(contexts)
        labels = np.asarray(labels)
        aspect_lens = np.asarray(aspect_lens)
        context_lens = np.asarray(context_lens)
        np.savez(save_fname, aspects=aspects, contexts=contexts, labels=labels, aspect_lens=aspect_lens, context_lens=context_lens)
        return save_fname

def load_word_embeddings(fname, embedding_dim, word2id):
    if not os.path.isfile(fname):
        raise IOError(ENOENT, 'Not a file', fname)

    word2vec = np.random.uniform(-0.01, 0.01, [len(word2id), embedding_dim])
    oov = len(word2id)
    with open(fname, 'r', encoding='utf-8') as f:
        for line in f:
            content = line.split(' ')
            if content[0] in word2id:
                word2vec[word2id[content[0]]] = np.array(list(map(float, content[1:])))
                oov = oov - 1
    word2vec[word2id['<pad>'], :] = 0
    print('There are %s words in vocabulary and %s words out of vocabulary' % (len(word2id) - oov, oov))
    return word2vec

