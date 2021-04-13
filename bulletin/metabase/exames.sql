SELECT TO_CHAR(nt.data_notificacao, 'DD/MM/YYYY') AS data_notificacao,
    nt.ibge_unidade_notifica,
    nt.metodo,
    nt.classificacao_final
FROM public.notificacao nt