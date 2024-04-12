#include <stdint.h>

void _wrapperSetActionCount(int i);
void _wrapperSetActionLabel(int i);

struct Matrix{
  int n, m;
  char *data;
};

void lts_type_set_state_length(void *type, int length);
void lts_type_set_state_name(void *type, int i, char *name);
void lts_type_set_state_typeno(void *type, int i, int tid);

void GBsetInitialState(void *model, int *initial);
void GBsetNextStateShort(void *model, void (*fn)());
void GBsetNextStateLong(void *model, void (*fn)());
void GBsetNextStateAll(void *model, void (*fn)());

void lts_type_set_state_label_count(void *type, int n);
void lts_type_set_state_label_name(void *type, int i, char *name);
void lts_type_set_state_label_typeno(void *type, int i, int n);

void GBsetStateLabelInfo(void *model, struct Matrix *mtx);
void GBsetStateLabelShort(void *model, void (*fn)());

typedef int (*StateLabelLongFn)(void *, int, void *);
void GBsetStateLabelLong(void *model, StateLabelLongFn fn);

typedef void (*StateLabelAllFn)(void *, void *, void *);
void GBsetStateLabelsAll(void *model, StateLabelAllFn fn);

void lts_type_set_edge_label_count(void *type, int n);
void lts_type_set_edge_label_name(void *type, int i, char *name);
void lts_type_set_edge_label_type(void *type, int i, char *name);
void lts_type_set_edge_label_typeno(void *type, int i, int tid);

void GBsetDMInfoRead(void *model, struct Matrix *mtx);
void GBsetDMInfoMayWrite(void *model, struct Matrix *mtx);
void GBsetDMInfoMustWrite(void *model, struct Matrix *mtx);
void GBsetDMInfo(void *model, struct Matrix *mtx);

struct Guard{
  int length;
  int labelID[];
};

void GBsetGuardsInfo(void *model, struct Guard **guards);
void GBsetGuard(void *model, int i, struct Guard *guard);
void GBsetGuardCoEnabledInfo(void *model, struct Matrix *mtx);
void GBsetCommutesInfo(void *model, struct Matrix *mtx);
void GBsetDoNotAccordInfo(void *model, struct Matrix *mtx);
void GBsetGuardNESInfo(void *model, struct Matrix *mtx);
void GBsetGuardNDSInfo(void *model, struct Matrix *mtx);

int lts_type_add_type(void *type, char *name, void *ptr);
void lts_type_set_format(void *type, int tid, int n);

struct Chunk{
  uint32_t len;
  char *str;
};

void GBchunkPut(void *model, int tid, struct Chunk chunk);

void dm_create(struct Matrix *mtx, int n, int m);
void dm_set(struct Matrix *mtx, int i, int j);
